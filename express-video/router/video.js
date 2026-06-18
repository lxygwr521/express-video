const express = require('express')
const router = express.Router()
const videoController = require('../controller/videoController')
const vodController = require('../controller/vodController')
const { verifyToken } = require('../util/jwt')
const { videoValidator } = require('../middleware/validator/videoValidator')
const multer = require('multer')
const upload = multer({ dest: 'public/' })

router
  .get('/gethots/:topnum', videoController.getHots)
  .post('/collect/:videoId', verifyToken(), videoController.collect)
  .post('/likelist', verifyToken(), videoController.likelist)
  .post('/dislike/:videoId', verifyToken(), videoController.dislikevideo)
  .post('/like/:videoId', verifyToken(), videoController.likevideo)
  .delete('/comment/:videoId/:commentId', verifyToken(), videoController.deletecomment)
  .post('/commentlist/:videoId', verifyToken(false), videoController.commentlist)
  .post('/comment/:videoId', verifyToken(), videoController.comment)
  .post('/videolist', videoController.videolist)
  .post('/myvideos', verifyToken(), videoController.getMyVideos)
  .delete('/:videoId', verifyToken(), videoController.deleteVideo)
  .get('/video/:videoId', verifyToken(false), videoController.video) //查数据库，拿"视频信息（作者 点赞量等）"
  .get('/getvod', verifyToken(), vodController.getvod)
  .get('/playinfo/:videoId', verifyToken(false), vodController.getPlayInfo) //调阿里云，拿"播放流" 返回的是给播放器用的数据：视频流地址。
  .post('/createvideo', verifyToken(), videoValidator, videoController.createvideo)
  .post('/coverimg', verifyToken(), upload.single('coverimg'), videoController.uploadCover)
module.exports = router
