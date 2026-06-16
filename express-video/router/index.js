const express = require('express')
const router = express.Router()
router.use('/user', require('./user'))
router.use('/video', require('./video'))
router.use('/message', require('./message'))
router.use('/vod', require('./vod'))
module.exports = router
