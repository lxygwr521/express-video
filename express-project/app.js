require('dotenv').config()
const express = require('express')
const cors = require('cors')
const morgan = require('morgan')
const router = require('./router')

const app = express()
// 请求体解析中间件，用于处理传入的请求体数据
app.use(express.json())
app.use(express.urlencoded())
//静态资源中间件
app.use(express.static('public'))
//跨域
app.use(cors())
//  Express 应用中注册 morgan 日志中间件，并使用 'dev' 格式输出请求日志。
//示例 GET /users 200 5.123 ms - 1024
app.use(morgan('dev'))

app.use('/api/v1', router)

// 路由级中间件：打印请求耗时
const timingMiddleware = (req, res, next) => {
  const start = Date.now()
  res.on('finish', () => {
    const duration = Date.now() - start
    console.log(`[${req.method}] ${req.originalUrl} - ${duration}ms`)
  })
  next()
}

// 测试路由（仅 /ping 受中间件影响）
app.get('/ping', timingMiddleware, (req, res) => {
  res.json({ message: 'pong', timestamp: Date.now() })
})

const PORT = process.env.PORT || 3000
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`)
})
