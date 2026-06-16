const express = require('express')
const router = express.Router()
const vodController = require('../controller/vodController')

// 阿里云 VOD 截图/事件回调（无需登录，由阿里云服务端调用）
router.post('/callback', vodController.vodCallback)

module.exports = router
