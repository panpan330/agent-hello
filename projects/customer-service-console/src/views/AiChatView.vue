<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { sendConsoleChatMessage, sendConsoleRagMessage } from '../services/aiChatApi'
import type { ChatHistoryMessage, RagCitation } from '../services/aiChatApi'

type ChatMode = 'agent' | 'rag'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  traceId?: string
  mode?: ChatMode
  citations?: RagCitation[]
}

const input = ref('A1001 物流一直没更新，帮我看看应该怎么处理')
const mode = ref<ChatMode>('agent')
const loading = ref(false)
const conversationId = ref<string>()
const lastTraceId = ref<string>()

const messages = ref<ChatMessage[]>([
  {
    id: 'welcome',
    role: 'assistant',
    text: '你好，我是 AI 客服助手。你可以使用 Agent 模式处理订单和工单，也可以切换到知识库 RAG 模式验证真实检索问答。',
  },
])

const history = computed<ChatHistoryMessage[]>(() =>
  messages.value
    .filter((message) => message.id !== 'welcome')
    .filter((message) => !message.citations)
    .map((message) => ({
      role: message.role,
      content: message.text,
    }))
    .slice(-20),
)

async function sendMessage() {
  const message = input.value.trim()
  if (!message || loading.value) {
    return
  }

  const userMessage: ChatMessage = {
    id: crypto.randomUUID(),
    role: 'user',
    text: message,
    mode: mode.value,
  }
  const requestHistory = history.value
  messages.value.push(userMessage)
  input.value = ''
  loading.value = true

  try {
    if (mode.value === 'rag') {
      const response = await sendConsoleRagMessage({
        query: message,
        candidateCount: 20,
        topN: 5,
      })
      lastTraceId.value = response.trace_id
      messages.value.push({
        id: crypto.randomUUID(),
        role: 'assistant',
        text: response.answer,
        traceId: response.trace_id,
        mode: 'rag',
        citations: response.citations,
      })
      return
    }

    const response = await sendConsoleChatMessage({
      message,
      conversationId: conversationId.value,
      history: requestHistory,
    })
    conversationId.value = response.conversation_id
    lastTraceId.value = response.trace_id
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      text: response.reply,
      traceId: response.trace_id,
      mode: 'agent',
    })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : 'AI 服务请求失败')
    messages.value.push({
      id: crypto.randomUUID(),
      role: 'assistant',
      text: '当前 AI 服务暂时不可用，请稍后再试，或联系人工客服处理。',
      mode: mode.value,
    })
  } finally {
    loading.value = false
  }
}

function formatCitation(citation: RagCitation) {
  const title = citation.title || citation.source
  const section = citation.section ? ` / ${citation.section}` : ''
  return `${citation.source_index}. ${title}${section}`
}
</script>

<template>
  <section class="chat-layout">
    <el-card class="chat-panel" shadow="never">
      <template #header>
        <div class="card-header">
          <span>AI 客服对话</span>
          <el-tag :type="mode === 'rag' ? 'warning' : 'success'">
            {{ mode === 'rag' ? '真实 RAG' : 'Agent' }}
          </el-tag>
        </div>
      </template>

      <div class="message-list">
        <div v-for="message in messages" :key="message.id" class="message-row" :class="message.role">
          <div class="message-bubble">
            {{ message.text }}
            <div v-if="message.citations?.length" class="citation-list">
              <strong>引用来源</strong>
              <span v-for="citation in message.citations" :key="citation.chunk_id">
                {{ formatCitation(citation) }}
              </span>
            </div>
            <span v-if="message.traceId" class="message-trace">trace_id: {{ message.traceId }}</span>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          resize="none"
          :disabled="loading"
          @keydown.ctrl.enter.prevent="sendMessage"
        />
        <el-button type="primary" :loading="loading" @click="sendMessage">发送</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>当前接口</template>
      <el-form label-position="top">
        <el-form-item label="回答模式">
          <el-radio-group v-model="mode">
            <el-radio-button label="agent">Agent</el-radio-button>
            <el-radio-button label="rag">知识库 RAG</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="Agent API">POST /api/ai/chat</el-descriptions-item>
        <el-descriptions-item label="RAG API">POST /api/ai/rag/ask</el-descriptions-item>
        <el-descriptions-item label="会话 ID">{{ conversationId || '首次发送后生成' }}</el-descriptions-item>
        <el-descriptions-item label="最近 trace">{{ lastTraceId || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </section>
</template>
