# Express → FastAPI 后端重构计划

## Context

将 express-video 项目的后端从 Node.js Express 重构为 Python FastAPI，目的：作为应聘 Python 后端实习的项目经验。

**重构范围**：31 个 REST 接口 + 3 个 WebSocket 事件 + Redis 热度排行 + 阿里云 VOD/OSS 集成  
**不变部分**：数据库（MySQL，表结构不变）、前端（Vue，接口路径和行为不变）、Redis（数据结构不变）

---

## 技术栈映射

| 能力 | 原 (Node.js) | 新 (Python) |
|------|-------------|-------------|
| Web 框架 | Express 4.x | FastAPI |
| ORM | Prisma | SQLAlchemy 2.x (async) |
| 数据校验 | express-validator | Pydantic v2 |
| 迁移工具 | prisma db push | Alembic |
| 认证 | jsonwebtoken | PyJWT |
| 密码哈希 | MD5 (自制 salt) | passlib + bcrypt (改用安全方案) |
| 文件上传 | multer | python-multipart |
| Redis | ioredis | redis-py (async) |
| WebSocket | socket.io | python-socketio |
| 阿里云 VOD | @alicloud/pop-core | alibabacloud-tea-openapi + 自定义 RPC 调用 |
| 阿里云 OSS | ali-oss | oss2 |
| 后台任务 | setTimeout/promise.catch | asyncio.create_task / BackgroundTasks |

---

## 项目目录结构

```
fastapi-video/                    # 新建目录，与原 express-video/express-video 并列
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口，挂载路由、中间件、WebSocket
│   ├── config.py                    # 配置（从 .env 读取，类型安全，Pydantic Settings）
│   ├── database.py                  # SQLAlchemy async engine + session 工厂
│   ├── models/                      # SQLAlchemy ORM 模型（对应 Prisma schema）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── video.py
│   │   ├── conversation.py
│   │   └── ...
│   ├── schemas/                     # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── video.py
│   │   └── ...
│   ├── api/                         # 路由（对应原 router/）
│   │   ├── __init__.py              # 主路由聚合
│   │   ├── user.py                  # /api/v1/user/*
│   │   ├── video.py                 # /api/v1/video/*
│   │   ├── vod.py                   # /api/v1/vod/*
│   │   └── message.py               # /api/v1/message/*
│   ├── services/                    # 业务逻辑层（新引入，比原 controller 更清晰）
│   │   ├── user_service.py
│   │   ├── video_service.py
│   │   ├── vod_service.py
│   │   ├── message_service.py
│   │   └── oss_service.py
│   ├── core/                        # 基础设施
│   │   ├── security.py              # JWT 创建/验证 + 密码哈希
│   │   ├── deps.py                  # FastAPI 依赖注入（get_db, get_current_user 等）
│   │   ├── redis.py                  # Redis 客户端 + Lua 脚本
│   │   ├── websocket.py             # python-socketio 事件处理
│   │   └── vod_client.py            # 阿里云 VOD RPC 客户端封装
│   └── middleware/
│       ├── cors.py
│       └── logging.py
├── alembic/                         # Alembic 迁移
│   └── versions/
├── tests/                           # 测试
├── .env
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 实施阶段（由易到难排序）

各阶段难度与依赖关系：

```
阶段1 骨架     [★☆☆]  零依赖
阶段2 模型     [★☆☆]  依赖骨架
阶段3 用户     [★★☆]  依赖模型+骨架
阶段4 Redis   [★★☆]  独立，不依赖业务模块
阶段5 VOD     [★★☆]  独立，纯 API 封装
阶段6 消息     [★★★]  依赖用户认证
阶段7 视频     [★★★] 依赖 Redis + VOD + 用户全就绪  ← 最难
阶段8 验证     [---]  收尾
```

---

### 阶段 1：项目骨架 + 基础设施（预计 4h）★☆☆

**文件**：`main.py`、`config.py`、`database.py`、`core/security.py`、`core/deps.py`

- FastAPI 应用初始化和生命周期管理
- Pydantic Settings 读取所有环境变量（DATABASE_URL、ALIYUN_*、OSS_*、REDIS_*、JWT_SECRET）
- SQLAlchemy async engine 建立，session 工厂
- JWT 创建/验证（保持 Token 格式不变，前端不用改）
- 密码哈希改用 bcrypt，但兼容旧 MD5 密码（双重验证：先 bcrypt，失败则 MD5 → 升迁为 bcrypt）
- 数据库依赖注入 `get_db()`，用户认证依赖 `get_current_user(required: bool = True)`

### 阶段 2：数据库模型（预计 3h）★☆☆

**文件**：`app/models/*.py`

按照原 Prisma schema 完整映射 8 个 SQLAlchemy 模型：
- User, Video, Videocomment, Videolike, Collect, Subscribe, Conversation, Message
- 保持表名和字段名与原数据库一致（`users`、`videos`、`videocomments`、`videolikes`、`collects`、`subscribes`、`conversations`、`messages`）
- 所有外键、唯一约束、索引保持一致
- 使用 `Mapped` + `mapped_column` 写法

**关键**：不重建数据库，直接连接已有的 MySQL 数据库。`__tablename__` 严格与原表名一致。

### 阶段 3：用户模块（预计 3h）★★☆

**文件**：`api/user.py`、`services/user_service.py`、`schemas/user.py`

迁移原 `userController.js` 的 8 个活跃函数（register, login, update, subscribe, unsubscribe, getchannel, getsubscribe, getuser）：

- 注册：Pydantic 校验 → bcrypt 哈希 → 写入 DB
- 登录：邮箱查 DB → 密码验证 → 生成 JWT
- 更新个人信息
- 订阅/取消订阅：DB 事务确保 subscribeCount 一致性
- 用户详情（含关注状态）
- 我的订阅列表 + 我的粉丝列表
- 头像上传（文件 → public/ 目录）

> 此时可验证：注册 + 登录拿到 Token，后续接口调试不再阻塞。

### 阶段 4：Redis 热度 + 状态管理（预计 2h）★★☆

**文件**：`core/redis.py`

- Redis 客户端连接（async）
- 热度增/删/排行（对应 redishotsinc.js）
- 3 个 Lua 脚本迁移（点赞/踩/收藏原子操作）— Lua 脚本本身不改，只改加载和调用方式
- Pipeline 查询用户状态（getUserVideoStatus）

> 独立模块，不依赖任何业务接口，可以单独写完单独测。视频模块（阶段 7）依赖此阶段就绪。

### 阶段 5：VOD 模块（预计 2h）★★☆

**文件**：`api/vod.py`、`services/vod_service.py`、`core/vod_client.py`

- 获取上传凭证（CreateUploadVideo）
- 获取播放信息（GetPlayInfo，按清晰度排序）
- 截图完成回调接收（vodCallback）
- 提交截图任务（SubmitSnapshotJob）

VOD Client 封装：使用 alibabacloud-tea-openapi 或手动构造 RPC 请求（HMAC-SHA1 签名 + 公共参数）

> 独立模块，纯阿里云 API 封装。视频模块（阶段 7）依赖此阶段就绪。

### 阶段 6：消息 + WebSocket（预计 3h）★★★

**文件**：`api/message.py`、`services/message_service.py`、`core/websocket.py`

- 会话列表 + 会话创建/查找
- 消息历史（分页）
- WebSocket 实时消息（python-socketio）：
  - connection 时 JWT 验证
  - join_conversation → 加入 room
  - send_message → 写 DB + 广播

> 依赖：用户认证（阶段 3）。

### 阶段 7：视频模块（预计 5h）★★★ — 工作量最大、依赖最多

**文件**：`api/video.py`、`services/video_service.py`、`schemas/video.py`

迁移原 `videoController.js` 的 14 个函数：

- 视频列表（分页，含作者信息 + 评论数）
- 视频详情（含点赞/踩/收藏/关注状态） ← 依赖 Redis 状态查询
- 创建视频（含封面 OSS 上传 + VOD 截图任务提交） ← 依赖 VOD
- 删除视频（DB 事务 + Redis 热度移除 + VOD 文件删除） ← 依赖 Redis + VOD
- 点赞/踩/收藏：与 Redis Lua 脚本交互 ← 依赖 Redis
- 评论列表（分页，含评论者关注状态）
- 评论创建/删除
- 热门排行（Redis sorted set） ← 依赖 Redis
- 封面上传 → OSS

> 依赖：用户模块 + Redis（阶段 4）+ VOD（阶段 5）全部就绪后才能完整实现。

### 阶段 8：验证与切换（预计 1h）

- 启动 python 后端（端口 3000），前端代理指向新后端
- 逐个接口测试：注册 → 登录 → 上传视频 → 列表 → 详情 → 点赞 → 评论 → 收藏 → 排行榜 → 消息
- 确保 WebSocket 消息推送正常
- 确保 VOD 截图回调链路正常

---

## 风险点与注意事项

| 风险 | 应对 |
|------|------|
| 阿里云 VOD Python SDK 不完善 | 使用 `httpx` 手动构造 RPC 签名请求（参考原 JS 版 `@alicloud/pop-core` 的实现） |
| 数据库字段名不一致 | SQLAlchemy `__tablename__` 严格对应 MySQL 表名，字段名用 `name='xxx'` 映射 |
| Redis Lua 脚本兼容性 | Lua 脚本原样迁移，只改 Python 调用方式（`redis.evalsha()`） |
| Socket.IO 跨语言兼容 | python-socketio 与前端 socket.io-client JS 版本兼容（均为 Socket.IO v4 协议） |
| bcrypt 与旧 MD5 共存 | 登录时先试 bcrypt，失败则用 MD5 验证，通过后自动将密码升级为 bcrypt |
| 异步代码复杂度 | FastAPI 原生 async，RPC 调用、DB 查询、Redis 操作全部异步，注意避免阻塞 |

---

## 验证方案

1. 启动 Python 后端 → `curl /ping` 返回 `{"message":"pong"}`
2. 注册/登录 → 拿到 JWT → 后续请求带 Token
3. 上传视频 → VOD 上传凭证正常 → 视频记录入库
4. 视频列表分页 → 返回正确 pageSize 条 + getvideoCount
5. 点赞/收藏 → Redis 热度实时更新 → 排行榜反映变化
6. WebSocket 消息 → 两个浏览器窗口打开，A 发消息 B 实时收到
7. VOD 截图回调 → 上传视频后封面自动出现在数据库中

---

## 总估时：约 23h（3-4 天全职）
