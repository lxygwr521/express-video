# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project name

一个视频分享社区平台，支持用户注册登录、通过阿里云 VOD 上传/播放视频、点赞收藏评论互动、以及基于 Redis 的热度排行榜。
待完成：用户之间发送消息  视频弹幕
## Project structure

```
express-video/              # Git repo root, open this in VSCode
├── express-video/          # Backend — Node.js Express API (port 3000)
│   ├── app.js              # Express entry point
│   ├── controller/         # Route handlers (userController, videoController, vodController)
│   ├── router/             # Express routes (user.js, video.js mounted at /api/v1)
│   ├── model/              # Prisma client singleton + Redis helpers
│   ├── middleware/          # express-validator wrappers (errorBack.js), JWT auth (util/jwt.js)
│   ├── util/               # JWT creation/verification, MD5 password hashing (salt: 'by')
│   ├── config/             # Hardcoded JWT secret + Redis connection config
│   ├── prisma/             # Schema (MySQL) + seed script
│   └── .env                # DATABASE_URL + Aliyun VOD credentials
└── frontend/               # Frontend — Vue 3 + Vite SPA (port 5173)
    └── src/
        ├── api/             # Axios instance + API modules (user.ts, video.ts)
        ├── stores/          # Pinia stores (auth, video, ui)
        ├── router/          # Vue Router with auth guards
        ├── views/           # Page components
        ├── components/      # Reusable components (VideoPlayer, CommentList, etc.)
        └── composables/     # useToast, usePagination
```

## Tech stack

| Layer | Technology |
|-------|-----------|
| **Backend runtime** | Node.js, Express 4.x |
| **Database ORM** | Prisma 6.x (MySQL) |
| **Cache** | Redis (ioredis) — video hot ranking |
| **Video hosting** | Aliyun VOD (upload, transcode, streaming, cover) |
| **Auth** | JWT (jsonwebtoken) |
| **Password hashing** | MD5 with static salt (util/md5.js) |
| **Validation** | express-validator 6.x |
| **File upload** | multer (avatar upload) |
| **HTTP client** | @alicloud/pop-core (Aliyun RPC) |
| **Frontend framework** | Vue 3 (Composition API + `<script setup>`) |
| **Build tool** | Vite 5.x |
| **Language** | TypeScript 5.x (frontend only) |
| **UI library** | Element Plus 2.x |
| **CSS** | Tailwind CSS 3.x |
| **State management** | Pinia 2.x |
| **Router** | Vue Router 4.x |
| **HTTP client** | Axios 1.x |
| **Dev tools** | nodemon (backend hot-reload), vue-tsc (type checking) |

## Commands

```bash
# Backend (express-video/express-video/)
npm run dev          # nodemon auto-restart on file change, port 3000
npx prisma db push   # Sync Prisma schema to MySQL
npx prisma seed      # Run seed script (5 users, 15 videos, sample data)
npx prisma generate  # Regenerate Prisma client after schema changes

# Frontend (express-video/frontend/)
npm run dev          # Vite dev server, port 5173, proxies /api → localhost:3000
npm run build        # Type-check + production build

# Utility
npx kill-port 3000   # Free port 3000 if backend didn't exit cleanly
```

## Architecture notes

### Auth flow
- Passwords hashed with MD5 + static salt `'by'` (`util/md5.js`, `util/password.js`)
- JWT signed with hardcoded secret in `config/config.default.js`, 24h expiry
- Token stored in `localStorage`, axios interceptor injects `Authorization: Bearer <token>`
- `verifyToken()` middleware decodes JWT and sets `req.user = { userinfo: { id, username, email, ... } }`
- `verifyToken(false)` allows optional auth (user may or may not be logged in)
- Controllers access current user via `req.user.userinfo.id`

### Video upload & VOD (Aliyun VOD)
- Frontend uploads video file directly to Aliyun VOD via the VOD upload SDK
- `vodController.getvod` calls `CreateUploadVideo` to get upload credentials
- `vodController.getPlayInfo` calls `GetPlayInfo` to get streaming URLs + `VideoBase.CoverURL`
- `createvideo` controller: after creating DB record, waits 5s then calls `GetVideoInfo` to fetch `Video.CoverURL` and write it back to the database. Cover is generated asynchronously by VOD — the 5s delay covers most cases.
- If no manual cover URL is provided and the video is VOD-uploaded, the cover is auto-fetched from VOD. Otherwise the `cover` field comes from `req.body.cover`.

### Video hot ranking (Redis)
- Single Redis sorted set key: `videohots`
- `hotInc(videoId, n)` adds `n` to a video's score (ZADD if new, ZINCRBY if exists)
- Scoring: view +1, like +2, comment +2, collect +3
- `topHots(n)` returns top N videos ranked by score descending (ZREVRANGE withscores)
- Redis config in `config/config.default.js` — host `127.0.0.1:6379`, password `root`
- On server start the Redis client connects and logs `Redis链接成功`

### Express-validator pattern
- `errorBack.js` wraps an array of `express-validator` chains into a middleware
- Runs all rules in parallel, returns 401 with `{ error: [{ msg, path }, ...] }` on failure
- Custom async validators use promises (e.g., check DB for duplicate email)
- Frontend processes the errors array: `errData.forEach(item => toast.error(item.msg))`

### HTTP status conventions
- 200/201: success
- 401: validation failure (express-validator), return format `{ error: [...] }`
- 402: auth failure (missing token, invalid token, wrong credentials)
- 404: resource not found
- 500: server error (caught exceptions, return format `{ err: error }` or `{ error: '...' }`)

### Key differences from production-ready patterns
- **MD5 passwords**: Not bcrypt/scrypt. Salt `'by'` is static, not per-user.
- **Hardcoded secrets**: JWT secret and Redis password are in `config/config.default.js`.
- **Express 4.x async errors**: Async route handlers without try-catch can cause unhandled rejections (requests hang instead of 500). Key handlers have been wrapped with try-catch, but not all.
- **No pagination defaults**: Some endpoints default to page 1, size 10 via destructuring.

### Pinia store pattern
- `auth.ts`: login/register/logout, persists user + token to localStorage, restores on app load
- `video.ts`: fetches video list, detail, hot ranking; toggleLike/toggleDislike/collect update `currentVideo` reactively
- Store actions call API modules in `src/api/*.ts`, which use the shared axios instance in `request.ts`