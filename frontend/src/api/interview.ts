/**
 * Echo Mock System - 面试场次 API 请求
 */

import request from '../utils/request'

export interface InterviewCreateRequest {
  target_role: string
}

export interface InterviewBrief {
  id: string
  target_role: string
  status: string
  start_time: string
  end_time: string | null
  overall_score: number | null
}

export interface MessageItem {
  id: string
  round_seq: number
  speaker: string
  content: string
  audio_file_path: string | null
  created_at: string
}

export interface InterviewDetail extends InterviewBrief {
  dimension_scores: Record<string, any> | null
  comprehensive_report: string | null
  messages: MessageItem[]
}

/** 创建面试场次 */
export const createInterview = (data: InterviewCreateRequest) =>
  request.post<any, InterviewBrief>('/interviews/', data)

/** 获取面试历史列表 */
export const listInterviews = () =>
  request.get<any, InterviewBrief[]>('/interviews/')

/** 获取面试场次详情 */
export const getInterviewDetail = (sessionId: string) =>
  request.get<any, InterviewDetail>(`/interviews/${sessionId}`)
