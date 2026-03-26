/**
 * Echo Mock System - 鉴权 API 请求
 */

import request from '../utils/request'

export interface RegisterRequest {
  username: string
  password: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: string
  username: string
}

/** 用户注册 */
export const register = (data: RegisterRequest) =>
  request.post<any, TokenResponse>('/auth/register', data)

/** 用户登录 */
export const login = (data: LoginRequest) =>
  request.post<any, TokenResponse>('/auth/login', data)

/** 获取当前用户信息 */
export const getMe = () =>
  request.get<any, UserInfo>('/auth/me')
