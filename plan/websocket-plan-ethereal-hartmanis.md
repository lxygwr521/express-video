# WebSocket 私聊功能实现方案

## Context

当前项目缺少用户之间实时通信能力。需要新增基于 WebSocket 的 1 对 1 私聊功能，支持消息实时送达、历史记录查询、会话列表管理。

## 技术选型

- **WebSocket 库**: `socket.io`（服务端）+ `socket.io-client`（前端）
  - 优势：自动重连、房间广播、ack 回调、开箱即用的 auth 中间件
  - 不使用原生 `ws`：缺少房间管理和重连机制

## 数据库设计

在 `prisma/schema.prisma` 中新增两个模型：

```prisma
model Conversation {
  id           Int       @id @default(autoincrement())
  user1Id      Int
  user2Id      Int
  lastMessage  String?   @db.Text
  updatedAt    DateTime  @updatedAt
  createdAt    DateTime  @default(now())

  user1        User      @relation("ConvUser1", fields: [user1Id], references: [id])
  user2        User      @relation("ConvUser2", fields: [user2Id], references: [id])
  messages     Message[]

  @@unique([user1Id, user2Id])
  @@map("conversations")
}

model Message {
  id             Int          @id @default(autoincrement())
  conversationId Int
  senderId       Int
  content        String       @db.Text
  createdAt      DateTime     @default(now())

  conversation   Conversation @relation(fields: [conversationId], references: [id])
  sender         User         @relation(fields: [senderId], references: [id])

  @@index([conversationId, createdAt])
  @@map("messages")
}
```

关键设计：
- `Conversation` 的 `@@unique([user1Id, user2Id])` 确保两个用户之间只有一条会话
- 业务层保证 `user1Id = min(idA, idB)`, `user2Id = max(idA, idB)`，无论谁发起查询都命中同一条记录
- `lastMessage` 反范式化字段，会话列表无需 join 消息表
- `Message` 的 `@@index([conversationId, createdAt])` 支持分页历史查询

## WebSocket 消息协议

| 方向 | 事件 | 载荷 | 说明 |
|------|------|------|------|
| Client → Server | `chat:send` | `{ toUserId, content }` | 发送消息，ack 返回 `{ success, message }` |
| Server → Client | `chat:message` | `{ id, conversationId, senderId, content, createdAt }` | 广播给收发双方 |
| Server → Client | `chat:conversation_update` | `{ conversationId, otherUserId, lastMessage, updatedAt }` | 更新会话列表 |
| Client → Server | `chat:typing` | `{ toUserId }` | 正在输入 |
| Server → Client | `chat:typing` | `{ fromUserId }` | 对方正在输入 |

连接认证：客户端连接时传 `auth: { token }`，服务端 `socket.io` middleware 用 `jsonwebtoken.verify` 解码 JWT，提取 `userId` 存入 `socket.data`。认证通过后自动加入房间 `user_${userId}`。

## 后端改动

### 1. 安装依赖
```bash
cd express-video && npm install socket.io
cd frontend && npm install socket.io-client
```

### 2. 改造 `app.js`
- `app.listen()` → `http.createServer(app).listen()`
- 导出 `server`，供 socket.io 附着
- 底部调用 `createSocketServer(server)` 初始化 WebSocket

### 3. 新建 `socket/index.js`
- 创建 `socket.io Server`，配置 CORS
- `io.use()` 实现 JWT auth middleware（复用 `config/config.default.js` 的 secret）
- 连接时加入 `user_${userId}` 房间
- 处理 `chat:send`：查/建 Conversation → 写 Message → 更新 lastMessage → 广播给双方
- 处理 `chat:typing`：转发给接收方

### 4. 新建 `controller/chatController.js`
- `getConversations`：查询当前用户相关的 Conversation，返回对方用户信息 + 最后消息
- `getMessages`：分页查询与指定用户的历史消息（按 `createdAt` 倒序取最新 N 条再反转）

### 5. 新建 `router/chat.js` + 挂载到 `router/index.js`
```js
router.get('/conversations', verifyToken(), chatController.getConversations)
router.get('/messages/:otherUserId', verifyToken(), chatController.getMessages)
```

## 前端改动

### 1. 新建 `types/chat.ts`
`ChatMessage` 和 `ConversationInfo` 接口

### 2. 新建 `api/chat.ts`
```ts
getConversations() → GET /chat/conversations
getMessages(otherUserId, page, pageSize) → GET /chat/messages/:otherUserId
```

### 3. 新建 `stores/chat.ts`（Pinia setup syntax）
- **状态**: `socket`, `connected`, `conversations`, `messages`, `currentOtherUserId`, `hasMore`, `typingUsers`
- **Socket 生命周期**: `connect()` / `disconnect()`，监听 `chat:message`、`chat:conversation_update`、`chat:typing`
- **API actions**: `fetchConversations()`, `openConversation(otherUserId)`, `loadMore()`
- **发送**: `sendMessage(content)` 通过 socket emit，`sendTyping()` 防抖发送

### 4. 新建 3 个组件
- **`ChatBubble.vue`**: 单条消息气泡，自己的右对齐蓝底，对方的左对齐灰底，带头像和时间
- **`ConversationList.vue`**: 会话列表侧边栏，每条显示头像+用户名+最后消息预览+时间
- **`ChatWindow.vue`**: 主聊天区，消息列表（自动滚底、"加载更多"）、输入框+发送按钮

### 5. 新建 `views/ChatView.vue`
左右分栏布局，左侧 ConversationList，右侧 ChatWindow。`onMounted` 连接 socket 并拉取会话列表。

### 6. 路由 + 导航入口
- 新增 `/chat` 和 `/chat/:userId` 路由（`requiresAuth`）
- `AppHeader.vue` 加"我的消息"按钮
- `UserProfileView.vue` 加"发消息"按钮 → 跳转 `/chat/:userId`

### 7. Socket 连接生命周期
- `App.vue` `onMounted`: 已登录则调用 `chatStore.connect()`
- `authStore.login()`: 登录成功后 connect
- `authStore.logout()`: disconnect

### 8. Vite 代理配置
`vite.config.ts` 新增 `/socket.io` 代理条目，开启 `ws: true`

## 实施顺序

| 步骤 | 内容 | 验证方式 |
|------|------|---------|
| 1 | 新增 Prisma 模型 → `prisma db push` | `npx prisma studio` 确认表存在 |
| 2 | 安装 `socket.io` / `socket.io-client` | package.json |
| 3 | 改造 `app.js` + 创建 `socket/index.js` | 启动后端，socket.io 无报错 |
| 4 | 创建 `chatController.js` + `router/chat.js` | curl 测试 REST 接口 |
| 5 | 创建前端 `types/chat.ts` → `api/chat.ts` → `stores/chat.ts` | 浏览器 console |
| 6 | 创建 `ChatBubble` → `ConversationList` → `ChatWindow` → `ChatView` | 页面渲染 |
| 7 | 路由 + AppHeader + UserProfile 入口 | 页面跳转 |
| 8 | Vite proxy + App.vue + authStore 生命周期 | 两个浏览器登录不同用户，对发消息 |

## 验证方案

1. 终端 A 登录用户 A，终端 B 登录用户 B
2. 用户 A 进入用户 B 主页 → 点击"发消息"
3. 发送消息 → 用户 B 实时收到（气泡出现）
4. 用户 B 回复 → 用户 A 实时收到
5. 刷新页面 → 历史消息仍然存在
6. 会话列表显示双方的最后一条消息预览
