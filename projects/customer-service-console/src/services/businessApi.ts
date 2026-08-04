import { javaApi } from './http'
import type { ApiResponse } from './http'

export interface OrderListItem {
  order_id: string
  owner_user_id: string
  order_status: string
  payment_status: string
  logistics_message: string
  latest_event: string
  can_create_ticket: boolean
  updated_at: string
}

export interface TicketListItem {
  ticket_id: string
  requester_user_id: string
  ticket_status: string
  title: string
  category: string
  priority: string
  related_order_id: string | null
  source: string
  created_at: string
  updated_at: string
}

export interface KnowledgeDocumentItem {
  document_id: string
  title: string
  doc_type: string
  business_domain: string
  permission_group: string
  status: string
  source_file_name: string
  chunk_count: number
  updated_by: string
  updated_at: string
}

function unwrapResponse<T>(response: ApiResponse<T>): T {
  if (!response.success) {
    throw new Error(response.message || response.code || '请求失败')
  }
  return response.data
}

export async function listOrders() {
  const response = await javaApi.get<ApiResponse<OrderListItem[]>>('/api/orders')
  return unwrapResponse(response.data)
}

export async function listTickets() {
  const response = await javaApi.get<ApiResponse<TicketListItem[]>>('/api/tickets')
  return unwrapResponse(response.data)
}

export async function listKnowledgeDocuments() {
  const response = await javaApi.get<ApiResponse<KnowledgeDocumentItem[]>>('/api/knowledge-documents')
  return unwrapResponse(response.data)
}
