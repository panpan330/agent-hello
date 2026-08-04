import { aiApi } from './http'
import type { ApiResponse } from './http'

export type ChatRole = 'user' | 'assistant'

export interface ChatHistoryMessage {
  role: ChatRole
  content: string
}

export interface ConsoleChatResponse {
  reply: string
  conversation_id: string
  trace_id: string
  mode: string
}

export interface RagCitation {
  source_index: number
  source: string
  title: string | null
  section: string | null
  chunk_id: string
  score: number
}

export interface ConsoleRagResponse {
  answer: string
  status: 'answered' | 'no_context'
  citations: RagCitation[]
  suggestions: string[]
  retrieved_count: number
  reranked_count: number
  used_rerank_fallback: boolean
  rerank_elapsed_ms: number
  collection_name: string
  embedding_model: string
  rerank_model: string
  llm_model: string
  trace_id: string
}

interface AiServiceErrorBody {
  code?: string
  message?: string
  trace_id?: string
}

export async function sendConsoleChatMessage(params: {
  message: string
  conversationId?: string
  history: ChatHistoryMessage[]
}) {
  try {
    const response = await aiApi.post<ConsoleChatResponse>('/api/ai/chat', {
      message: params.message,
      conversation_id: params.conversationId,
      history: params.history,
    })
    return response.data
  } catch (error: any) {
    throw buildAiServiceError(error, 'AI 服务请求失败')
  }
}

export async function sendConsoleRagMessage(params: {
  query: string
  candidateCount?: number
  topN?: number
}) {
  try {
    const response = await aiApi.post<ConsoleRagResponse>('/api/ai/rag/ask', {
      query: params.query,
      candidate_count: params.candidateCount || 20,
      top_n: params.topN || 5,
    })
    return response.data
  } catch (error: any) {
    throw buildAiServiceError(error, 'RAG 知识库问答请求失败')
  }
}

function buildAiServiceError(error: any, fallbackMessage: string) {
  const data = error?.response?.data as AiServiceErrorBody | ApiResponse<unknown> | undefined
  if (data && typeof data === 'object' && 'message' in data && typeof data.message === 'string') {
    return new Error(data.message)
  }
  return new Error(fallbackMessage)
}
