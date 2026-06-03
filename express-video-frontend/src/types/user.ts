export interface User {
  _id: number
  username: string
  email: string
  phone: string
  image: string | null
  channeldes: string | null
  subscribeCount: number
  createAt?: string
  updateAt?: string
  isSubscribe?: boolean
}

export interface UserWithToken extends Omit<User, 'password'> {
  token: string
}

export interface LoginForm {
  email: string
  password: string
}

export interface RegisterForm {
  username: string
  email: string
  phone: string
  password: string
}

export interface UpdateUserForm {
  username?: string
  email?: string
  phone?: string
  password?: string
  image?: string
  channeldes?: string
}
