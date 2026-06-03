const md5 = require('./md5')

module.exports.hashPassword = (plain) => md5(plain)

module.exports.verifyPassword = (plain, hash) => md5(plain) === hash
