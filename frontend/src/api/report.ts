/**
 * Echo Mock System - 报告 API 请求
 */

import request from '../utils/request'

export interface DimensionScore {
  name: string
  score: number
}

export interface QaEvaluationItem {
  id: string
  question_content: string
  user_answer: string | null
  audio_analysis_status: string
  speech_rate: number | null
  pause_ratio: number | null
  technical_score: number | null
  correction_feedback: string | null
}

export interface ReportResponse {
  session_id: string
  target_role: string
  status: string
  overall_score: number | null
  dimension_scores: DimensionScore[] | null
  comprehensive_report: string | null
  evaluations: QaEvaluationItem[]
}

/** 获取面试综合报告 */
export const getReport = (sessionId: string) =>
  request.get<any, ReportResponse>(`/reports/${sessionId}`)
