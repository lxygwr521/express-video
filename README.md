# Express Video

一个视频分享社区平台 — 支持用户注册登录、阿里云 VOD 视频上传/播放、点赞收藏评论互动、实时聊天（Socket.IO）以及基于 Redis 的热度排行榜。

## 功能

- 用户注册/登录（JWT + bcrypt 密码哈希）
- 视频上传（阿里云 VOD）、转码、播放
- 封面图片管理（阿里云 OSS 存储）
- 点赞/点踩/收藏/评论（MySQL + Redis 双写）
- 视频热度排行榜（Redis Sorted Set，观看/点赞/评论/收藏计分）
- 用户关注/取关
- 实时私信聊天（Socket.IO）
- 个人频道、头像上传

## 技术栈

| 层 | 技术 |
|---|------|
| **后端框架** | Python 3.12, FastAPI (ASGI) |
| **ASGI 服务器** | Uvicorn |
| **数据库 ORM** | SQLAlchemy 2.0 (async, aiomysql) |
| **缓存** | Redis (排行榜、用户状态、Lua 原子操作) |
| **视频服务** | 阿里云 VOD (上传/转码/播放/封面截图) |
| **图片存储** | 阿里云 OSS |
| **认证** | PyJWT + bcrypt (passlib) |
| **实时通信** | python-socketio (Socket.IO) |
| **校验** | Pydantic 2.x |
| **前端** | Vue 3 + TypeScript + Vite |
| **UI 库** | Element Plus + Tailwind CSS |
| **状态管理** | Pinia |

## 项目结构

```
express-video/
├── fastapi-video/          # 后端 — Python FastAPI (端口 3000)
│   ├── requirements.txt
│   ├── .env                # 本地开发环境变量
│   └── app/
│       ├── main.py         # 应用入口
│       ├── config.py       # 配置 (Pydantic Settings)
│       ├── database.py     # 异步数据库引擎
│       ├── api/            # 路由层 (user, video, vod, message)
│       ├── models/         # SQLAlchemy ORM 模型
│       ├── schemas/        # Pydantic 请求/响应校验
│       ├── services/       # 业务逻辑层
│       ├── core/           # 基础设施 (auth, redis, oss, vod, websocket)
│       └── middleware/     # 自定义中间件
├── express-video/          # [旧] Node.js Express 后端 (已弃用，保留作参考)
├── frontend/               # 前端 — Vue 3 + Vite (端口 5173)
│   └── src/
│       ├── api/            # Axios 实例 + API 模块
│       ├── stores/         # Pinia 状态管理
│       ├── router/         # Vue Router (含 auth 守卫)
│       ├── views/          # 页面组件
│       └── components/     # 可复用组件
├── docker-compose.yml      # Docker 编排 (MySQL + Redis + 后端 + 前端)
├── .env.docker.example     # Docker 环境变量模板 (可安全提交到 Git)
└── plan/                   # 开发计划文档
```

## 快速开始

### 方式一：Docker（推荐，一键启动）

```bash
# 1. 克隆项目
git clone https://github.com/lxygwr521/express-video.git
cd express-video

# 2. 配置环境变量
cp .env.docker.example .env
# 编辑 .env，填入你的阿里云密钥（不填也能使用核心功能，见下方说明）

# 3. 启动
docker-compose up -d

# 4. 访问
# 前端: http://localhost:8080
# 后端 API: http://localhost:3001
```

首次启动会自动创建数据库表。

### 方式二：本地开发

**前置条件：** MySQL 8.0+、Redis 7+、Python 3.12+、Node.js 20+

```bash
# 1. 启动 MySQL 和 Redis
docker-compose up -d mysql redis

# 2. 后端
cd fastapi-video
cp .env.example .env        # 编辑 .env 配置数据库连接
pip install -r requirements.txt
uvicorn app.main:app --port 3000 --reload

# 3. 前端 (新终端)
cd frontend
npm install
npm run dev                  # http://localhost:5173
```

## 阿里云密钥说明

| 不需要密钥 | 需要密钥 |
|-----------|---------|
| 注册/登录 | 视频上传 |
| 浏览视频列表 | 视频播放链接 |
| 点赞/收藏/评论 | 头像/封面上传 |
| 实时聊天 | VOD 回调 |
| 用户关注 | |

不填阿里云密钥，核心的浏览互动功能完全正常。只需在 `.env` 中将以下变量留空即可：

```ini
ALIYUN_ACCESS_KEY_ID=
ALIYUN_ACCESS_KEY_SECRET=
OSS_BUCKET=
```

## API 概览

所有接口前缀：`/api/v1`

### 用户 ` /user`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/registers` | 注册 | - |
| POST | `/logins` | 登录 | - |
| GET | `/getchannel` | 获取当前用户频道 | 可选 |
| GET | `/getuser/{userId}` | 获取用户信息 | 可选 |
| GET | `/getsubscribe/{userId}` | 获取用户订阅列表 | - |
| PUT | `/` | 更新个人信息 | 必须 |
| POST | `/headimg` | 上传头像 | 必须 |
| POST | `/subscribe/{userId}` | 关注用户 | 必须 |
| POST | `/unsubscribe/{userId}` | 取消关注 | 必须 |

### 视频 ` /video`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/videolist` | 视频列表（分页） | - |
| GET | `/video/{videoId}` | 视频详情 | 可选 |
| GET | `/gethots/{topnum}` | 热度排行榜 | - |
| POST | `/createvideo` | 发布视频 | 必须 |
| POST | `/myvideos` | 我的视频（分页） | 必须 |
| DELETE | `/{videoId}` | 删除视频 | 必须 |
| POST | `/coverimg` | 手动上传封面 | 必须 |
| POST | `/like/{videoId}` | 点赞 | 必须 |
| POST | `/dislike/{videoId}` | 点踩 | 必须 |
| POST | `/collect/{videoId}` | 收藏切换 | 必须 |
| POST | `/likelist` | 我的点赞列表 | 必须 |
| POST | `/comment/{videoId}` | 发表评论 | 必须 |
| POST | `/commentlist/{videoId}` | 评论列表（分页） | - |
| DELETE | `/comment/{videoId}/{commentId}` | 删除评论 | 必须 |
| GET | `/getvod` | 获取上传凭证 | 必须 |
| GET | `/playinfo/{videoId}` | 获取播放信息 | - |

### 消息 ` /message`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/conversations` | 会话列表 | 必须 |
| GET | `/conversation/{userId}` | 与某用户的会话 | 必须 |
| GET | `/messages/{conversationId}` | 会话消息记录 | 必须 |

消息**实时收发**通过 Socket.IO WebSocket 实现（与 HTTP 共用端口 3000）。

### VOD 回调 ` /vod`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/callback` | 阿里云 VOD 回调 (封面自动更新) |

## HTTP 状态码约定

| 状态码 | 含义 |
|--------|------|
| 200/201 | 成功 |
| 401 | 请求参数校验失败 (Pydantic) |
| 402 | 认证失败 (未登录 / token 无效) |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## License

MIT
