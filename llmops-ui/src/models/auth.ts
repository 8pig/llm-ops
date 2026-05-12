import { type BaseResponse } from './base'

// 账号密码登录响应结构
export type PasswordLoginResponse = BaseResponse<{
  access_token: string
  expire_at: number
}>
