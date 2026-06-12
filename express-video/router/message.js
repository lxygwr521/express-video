const express = require('express')
const router = express.Router()
const messageController = require('../controller/messageController')
const { verifyToken } = require('../util/jwt')

router
  .get('/conversations', verifyToken(), messageController.getConversations)
  .get('/conversation/:userId', verifyToken(), messageController.getOrCreateConversation)
  .get('/messages/:conversationId', verifyToken(), messageController.getMessages)

module.exports = router
