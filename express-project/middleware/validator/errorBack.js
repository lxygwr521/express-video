// 从 express-validator 引入校验结果提取函数
const { validationResult } = require('express-validator')

// 封装校验中间件：接收一组校验规则数组，返回 Express 中间件
module.exports = validator => {
  return async (req, res, next) => {
    // 并行执行所有校验规则（每个规则通过 .run(req) 将校验结果写入 req 中）
    await Promise.all(validator.map(validate => validate.run(req)))
    // 从请求中提取校验结果
    const errors = validationResult(req)
    // 如果存在校验失败项，直接返回 401 及错误详情，不再进入下一中间件
    if (!errors.isEmpty()) {
      return res.status(401).json({ error: errors.array() })
    }
    // 校验通过，放行到下一个中间件/控制器
    next()
  }
}