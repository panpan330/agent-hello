import { aiApi } from './http'

export type KnowledgeBaseEmbeddingMode = 'fake' | 'real'

export interface KnowledgeBaseDocumentStatus {
  source: string
  title: string
  file_name: string
  file_extension: string
  doc_type: string | null
  business_domain: string | null
  permission_group: string | null
}

export interface KnowledgeBaseStatusResponse {
  documents: KnowledgeBaseDocumentStatus[]
  document_count: number
  collection_name: string
  qdrant_base_url: string
  fake_embedding_dimension: number
  real_embedding_configured: boolean
  trace_id: string
}

export interface KnowledgeBaseIngestRequest {
  embedding_mode: KnowledgeBaseEmbeddingMode
  refresh: boolean
  wait: boolean
  include_readme: boolean
  chunk_size: number
  chunk_overlap: number
}

export interface KnowledgeBaseIngestResponse {
  embedding_mode: KnowledgeBaseEmbeddingMode
  document_count: number
  chunk_count: number
  vector_count: number
  vector_dimension: number
  collection_name: string
  replaced_source_count: number
  trace_id: string
}

interface AiServiceErrorBody {
  code?: string
  message?: string
  trace_id?: string
}

export async function getKnowledgeBaseStatus() {
  try {
    const response = await aiApi.get<KnowledgeBaseStatusResponse>('/api/knowledge-base/status')
    return response.data
  } catch (error: any) {
    throw buildAiServiceError(error, '知识库状态加载失败')
  }
}

export async function ingestKnowledgeBase(request: KnowledgeBaseIngestRequest) {
  try {
    const response = await aiApi.post<KnowledgeBaseIngestResponse>('/api/knowledge-base/ingest', request)
    return response.data
  } catch (error: any) {
    throw buildAiServiceError(error, '知识库入库失败')
  }
}

function buildAiServiceError(error: any, fallbackMessage: string) {
  const data = error?.response?.data as AiServiceErrorBody | undefined
  if (data?.message) {
    return new Error(data.message)
  }
  return new Error(fallbackMessage)
}
