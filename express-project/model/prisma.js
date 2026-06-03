const { PrismaClient } = require('@prisma/client')

const prisma = new PrismaClient().$extends({
  result: {
    user: {
      _id: { needs: { id: true }, compute(u) { return u.id } },
    },
    video: {
      _id: { needs: { id: true }, compute(v) { return v.id } },
    },
    subscribe: {
      _id: { needs: { id: true }, compute(s) { return s.id } },
    },
    videocomment: {
      _id: { needs: { id: true }, compute(c) { return c.id } },
    },
    videolike: {
      _id: { needs: { id: true }, compute(l) { return l.id } },
    },
    collect: {
      _id: { needs: { id: true }, compute(c) { return c.id } },
    },
  },
})

module.exports = prisma
