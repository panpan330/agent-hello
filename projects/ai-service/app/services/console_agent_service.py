from dataclasses import dataclass
from threading import Lock
from collections.abc import Iterator
import json
import logging
from typing import Any, Protocol

import httpx
from langgraph.checkpoint.redis import RedisSaver
from redis.exceptions import RedisError

from app.agents.ticket_agent import (
    LLMTicketFields,
    TICKET_CONFIRMATION_INTERRUPT_KIND,
    TicketFields,
    build_ticket_agent_input,
    build_pending_ticket_confirmation,
    build_ticket_agent_graph_for_model_mode,
    build_ticket_agent_thread_config,
    create_java_cancel_executor,
    create_java_refund_executor,
    get_ticket_confirmation_interrupt_payload,
    find_missing_ticket_fields,
    resume_ticket_confirmation_interrupt,
    run_ticket_agent_in_thread,
)
from app.core.ai_security_boundary import redact_sensitive_text
from app.core.business_context import reset_business_context, set_business_context
from app.core.config import Settings
from app.core.exceptions import AppException
from app.core.trace import build_trace_headers, get_trace_id
from app.rag.embeddings import OpenAICompatibleEmbeddingModel
from app.rag.generator import RagAnswer, create_rag_answer_service
from app.rag.rerank import (
    HttpReranker,
    make_rerank_candidates_from_retrieved_chunks,
    rerank_with_fallback,
    reranked_chunks_to_retrieved_chunks,
)
from app.rag.retriever import retrieve_top_k
from app.rag.vector_store import QdrantVectorStore
from app.schemas.console_agent import (
    ConsoleAgentConversation,
    ConsoleAgentConversationSummary,
    ConsoleAgentFeedbackRequest,
    ConsoleAgentFeedbackResponse,
    ConsoleAgentResponse,
    ConsoleAgentHumanHandoff,
    ConsoleAgentTicketConfirmation,
    ConsoleAgentTicketFields,
)
from app.schemas.ticket import CreatedTicket
from app.services.java_ticket_client import JavaTicketClient
from app.services.java_feedback_client import JavaFeedbackClient
from app.services.console_agent_conversation_store import ConsoleAgentConversationStore
from app.tools.fake_order_tool import query_order


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConsoleAgentActor:
    user_id: str
    tenant_id: str
    roles: tuple[str, ...]


AGENT_PROGRESS_BY_NODE: dict[str, tuple[str, str]] = {
    "normalize_user_input": ("preparing", "正在准备本次请求"),
    "supervisor_route": ("analyzing", "正在分析问题类型"),
    "classify_intent": ("analyzing", "正在分析问题类型"),
    "retrieve_policy": ("knowledge_search", "正在检索知识库"),
    "decide_ticket_need": ("planning", "正在规划处理方式"),
    "query_order": ("order_lookup", "正在查询订单信息"),
    "extract_ticket_fields": ("ticket_draft", "正在整理工单信息"),
    "handle_refund_request": ("refund_draft", "正在整理退款信息"),
    "handle_cancel_request": ("cancel_draft", "正在整理取消订单信息"),
    "ask_missing_ticket_fields": ("need_details", "正在确认需要补充的信息"),
    "request_ticket_confirmation": ("confirmation", "正在准备工单确认"),
    "create_ticket": ("ticket_creation", "正在创建工单"),
    "execute_refund_request": ("refund_execution", "正在执行退款"),
    "execute_cancel_request": ("cancel_execution", "正在执行取消订单"),
    "build_direct_answer": ("answering", "正在整理回复"),
    "build_unsupported_answer": ("answering", "正在整理回复"),
    "ask_clarifying_question": ("need_details", "正在确认需要补充的信息"),
}

HUMAN_HANDOFF_BLOCKED_ORDER_ERROR_CODES = frozenset(
    {"ORDER_ACCESS_DENIED", "ORDER_NOT_FOUND", "ORDER_ID_INVALID"}
)


def build_agent_progress_event(node_name: str) -> dict[str, str] | None:
    if node_name == "__interrupt__":
        return {"stage": "waiting_confirmation", "label": "等待你的确认"}
    progress = AGENT_PROGRESS_BY_NODE.get(node_name)
    if progress is None:
        return None
    stage, label = progress
    return {"stage": stage, "label": label}


class ConsoleAgentActorResolver(Protocol):
    def resolve(self, authorization: str | None) -> ConsoleAgentActor:
        """Resolve the caller from the Java business service authentication boundary."""


class JavaConsoleAgentActorResolver:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve(self, authorization: str | None) -> ConsoleAgentActor:
        if not authorization or not authorization.strip():
            raise AppException(
                code="AUTH_REQUIRED",
                message="Please sign in before using the AI customer service.",
                status_code=401,
            )

        base_url = self.settings.resolved_java_business_service_base_url
        try:
            with httpx.Client(base_url=base_url, timeout=self.settings.resolved_java_business_service_timeout_seconds) as client:
                response = client.get(
                    "/api/auth/me",
                    headers={
                        "Authorization": authorization,
                        **build_trace_headers(),
                    },
                )
        except httpx.RequestError as exc:
            raise AppException(
                code="AUTH_SERVICE_UNAVAILABLE",
                message="The account service is temporarily unavailable. Please try again later.",
                status_code=502,
            ) from exc

        if response.status_code == 401:
            raise AppException(
                code="AUTH_REQUIRED",
                message="Your sign-in has expired. Please sign in again.",
                status_code=401,
            )
        if response.status_code != 200:
            raise AppException(
                code="AUTH_SERVICE_REJECTED",
                message="The account service could not verify the current user.",
                status_code=502,
            )

        try:
            payload = response.json()
            data = payload["data"]
            user_id = str(data["user_id"]).strip()
            tenant_id = str(data["tenant_id"]).strip()
            roles = tuple(str(role).strip() for role in data["roles"] if str(role).strip())
        except (KeyError, TypeError, ValueError) as exc:
            raise AppException(
                code="AUTH_SERVICE_RESPONSE_INVALID",
                message="The account service returned an invalid user identity response.",
                status_code=502,
            ) from exc

        if not user_id or not tenant_id:
            raise AppException(
                code="AUTH_SERVICE_RESPONSE_INVALID",
                message="The account service returned an incomplete user identity response.",
                status_code=502,
            )
        return ConsoleAgentActor(user_id=user_id, tenant_id=tenant_id, roles=roles)


_TICKET_CONFIRMATION_PENDING_NEXT_NODES = frozenset(
    {"request_ticket_confirmation", "ticket_agent"}
)


def _has_pending_ticket_confirmation_next(snapshot: Any) -> bool:
    """Whether a snapshot is paused waiting for a ticket confirmation decision.

    单 Agent 图：顶层 next 直接含 "request_ticket_confirmation"。
    多 Agent 监督图：确认中断发生在 ticket worker 子图内部，顶层 next 为
    ("ticket_agent",)，两者都代表有待决工单确认。
    """
    return bool(set(snapshot.next) & _TICKET_CONFIRMATION_PENDING_NEXT_NODES)


def _pending_confirmation_fields(snapshot: Any) -> dict | None:
    """Resolve the confirmed ticket draft from a state snapshot.

    优先级：活动中的确认中断（interrupt payload）优先，顶层 ticket_fields 兜底。
    多 Agent 模式下 worker 子图完成会把 ticket_fields 写回顶层；同一会话第二张
    待确认工单中断时顶层仍是上一轮旧草稿，若先读顶层会用旧字段算出错误
    confirmation_id，导致确认流程误抛 TICKET_CONFIRMATION_MISMATCH。
    单 Agent 图中断时 interrupts payload 与顶层 ticket_fields 指向同一份草稿，
    调整优先级后行为不变。
    """
    for interrupt in getattr(snapshot, "interrupts", ()) or ():
        value = getattr(interrupt, "value", None)
        if not isinstance(value, dict):
            continue
        pending = value.get("pending_ticket_confirmation")
        if isinstance(pending, dict) and isinstance(pending.get("ticket_fields"), dict):
            return pending["ticket_fields"]
    fields = snapshot.values.get("ticket_fields")
    if isinstance(fields, dict):
        return fields
    return None


class ProductionPolicyRagService:
    """Adapter that lets the Agent reuse the production embedding, Qdrant, and rerank chain."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def answer_policy_question(self, query: str) -> RagAnswer:
        try:
            embedding_model = OpenAICompatibleEmbeddingModel.from_settings(self.settings)
        except ValueError as exc:
            raise AppException(
                code="RAG_EMBEDDING_CONFIG_MISSING",
                message="RAG embedding configuration is incomplete.",
                status_code=500,
            ) from exc

        try:
            reranker = HttpReranker.from_settings(self.settings)
        except ValueError as exc:
            raise AppException(
                code="RAG_RERANK_CONFIG_MISSING",
                message="RAG rerank configuration is incomplete.",
                status_code=500,
            ) from exc

        retrieved_chunks = retrieve_top_k(
            query,
            embedding_model=embedding_model,
            vector_store=QdrantVectorStore.from_settings(self.settings),
            top_k=self.settings.rerank_candidate_count,
        )
        rerank_result = rerank_with_fallback(
            query,
            make_rerank_candidates_from_retrieved_chunks(retrieved_chunks),
            primary_reranker=reranker,
            top_k=self.settings.rerank_top_n,
        )
        return create_rag_answer_service(self.settings).generate_answer_with_citations(
            query,
            chunks=reranked_chunks_to_retrieved_chunks(rerank_result.results),
        )


class ConsoleAgentService:
    def __init__(
        self,
        settings: Settings,
        *,
        graph: Any | None = None,
        conversation_store: ConsoleAgentConversationStore | None = None,
        feedback_client: JavaFeedbackClient | None = None,
    ) -> None:
        self.settings = settings
        self._graph = graph
        self._graph_lock = Lock()
        self._checkpointer_context: Any | None = None
        self._conversation_store = conversation_store
        self._feedback_client = feedback_client

    @property
    def graph(self) -> Any:
        if self._graph is None:
            with self._graph_lock:
                if self._graph is None:
                    self._graph = self._build_graph()
        return self._graph

    def _build_graph(self) -> Any:
        ticket_creator, order_query_executor, refund_executor, cancel_executor = (
            self._build_tool_dependencies()
        )
        if self.settings.agent_multi_agent_enabled:
            from app.agents.supervisor.supervisor_graph import build_supervisor_graph

            return build_supervisor_graph(
                knowledge_service=ProductionPolicyRagService(self.settings),
                order_query_executor=order_query_executor,
                ticket_creator=ticket_creator,
                refund_executor=refund_executor,
                cancel_executor=cancel_executor,
                checkpointer=self._create_redis_checkpointer(),
                interrupt_confirmation=True,
            )
        return build_ticket_agent_graph_for_model_mode(
            ticket_creator=ticket_creator,
            policy_rag_service=ProductionPolicyRagService(self.settings),
            order_query_executor=order_query_executor,
            refund_executor=refund_executor,
            cancel_executor=cancel_executor,
            mode=self.settings.ticket_agent_model_mode,
            settings=self.settings,
            checkpointer=self._create_redis_checkpointer(),
            interrupt_confirmation=True,
        )

    def _build_tool_dependencies(self) -> tuple[Any, Any, Any, Any]:
        if self.settings.agent_mcp_tools_enabled:
            from app.agents.mcp_tool_adapters import (
                create_mcp_cancel_executor,
                create_mcp_order_query_executor,
                create_mcp_refund_executor,
                create_mcp_ticket_creator,
            )

            return (
                create_mcp_ticket_creator(self.settings),
                create_mcp_order_query_executor(self.settings),
                create_mcp_refund_executor(self.settings),
                create_mcp_cancel_executor(self.settings),
            )
        from app.tools.fake_order_tool import query_order

        return (
            JavaTicketClient.from_settings(self.settings),
            lambda arguments: query_order(arguments, settings=self.settings),
            create_java_refund_executor(),
            create_java_cancel_executor(),
        )

    def close(self) -> None:
        if self._checkpointer_context is not None:
            self._checkpointer_context.__exit__(None, None, None)
            self._checkpointer_context = None
        if self._conversation_store is not None:
            self._conversation_store.close()
            self._conversation_store = None

    @property
    def conversation_store(self) -> ConsoleAgentConversationStore:
        if self._conversation_store is None:
            self._conversation_store = ConsoleAgentConversationStore(self.settings)
        return self._conversation_store

    @property
    def feedback_client(self) -> JavaFeedbackClient:
        if self._feedback_client is None:
            self._feedback_client = JavaFeedbackClient.from_settings(self.settings)
        return self._feedback_client

    def _create_redis_checkpointer(self) -> RedisSaver:
        context = RedisSaver.from_conn_string(
            self.settings.resolved_agent_redis_url,
            ttl={
                "default_ttl": self.settings.agent_checkpoint_ttl_minutes,
                "refresh_on_read": True,
            },
            checkpoint_prefix=f"{self.settings.resolved_agent_checkpoint_key_prefix}:checkpoint",
            checkpoint_write_prefix=(
                f"{self.settings.resolved_agent_checkpoint_key_prefix}:checkpoint-write"
            ),
        )
        try:
            checkpointer = context.__enter__()
            checkpointer.setup()
        except (RedisError, OSError, ValueError) as exc:
            context.__exit__(type(exc), exc, exc.__traceback__)
            raise AppException(
                code="AGENT_STATE_STORE_UNAVAILABLE",
                message="The AI conversation state service is temporarily unavailable.",
                status_code=503,
            ) from exc

        self._checkpointer_context = context
        return checkpointer

    def reply(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        message: str,
    ) -> ConsoleAgentResponse:
        thread_id = self._thread_id(actor, conversation_id)
        self._reject_if_confirmation_is_pending(thread_id)
        from app.agents.langsmith_tracing import build_ticket_agent_langsmith_trace_context
        from app.agents.tracing_spans import start_agent_span

        trace_context = build_ticket_agent_langsmith_trace_context(
            {"user_message": message},
            operation="console_agent_reply",
            thread_id=thread_id,
            actor_id=actor.user_id,
            extra_tags=["console-agent"],
        )
        graph_config = trace_context.to_langgraph_config()
        with start_agent_span(
            intent=None,
            thread_id=thread_id,
            conversation_id=conversation_id,
        ):
            tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
            try:
                state = run_ticket_agent_in_thread(
                    self.graph,
                    message,
                    thread_id=thread_id,
                    actor_id=actor.user_id,
                    config=graph_config,
                )
            finally:
                reset_business_context(tokens)
        response = self._to_response(state, conversation_id=conversation_id)
        self._record_exchange(
            actor=actor,
            conversation_id=conversation_id,
            user_message=message,
            response=response,
        )
        return response

    def stream_reply(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        message: str,
        trace_id: str,
    ) -> Iterator[dict[str, Any]]:
        yield {
            "event": "start",
            "data": {"trace_id": trace_id, "conversation_id": conversation_id},
        }
        thread_id = self._thread_id(actor, conversation_id)
        from app.agents.langsmith_tracing import build_ticket_agent_langsmith_trace_context
        from app.agents.tracing_spans import set_span_status_error, start_agent_span

        trace_context = build_ticket_agent_langsmith_trace_context(
            {"user_message": message},
            operation="console_agent_stream",
            thread_id=thread_id,
            actor_id=actor.user_id,
            extra_tags=["console-agent"],
        )
        graph_config = trace_context.to_langgraph_config()
        context_tokens = None
        interrupt_payload: Any | None = None
        with start_agent_span(
            intent=None,
            thread_id=thread_id,
            conversation_id=conversation_id,
        ):
            try:
                self._reject_if_confirmation_is_pending(thread_id)
                context_tokens = set_business_context(
                    user_id=actor.user_id,
                    tenant_id=actor.tenant_id,
                )
                for update in self.graph.stream(
                    build_ticket_agent_input(message) | {"ticket_actor_id": actor.user_id},
                    config={**build_ticket_agent_thread_config(thread_id), **graph_config},
                    stream_mode="updates",
                ):
                    for node_name, node_update in update.items():
                        if node_name == "__interrupt__":
                            interrupt_payload = node_update
                        progress_event = build_agent_progress_event(node_name)
                        if progress_event is not None:
                            yield {"event": "stage", "data": progress_event}

                snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
                state = dict(snapshot.values)
                if interrupt_payload is not None:
                    state["__interrupt__"] = interrupt_payload
                response = self._to_response(
                    state,
                    conversation_id=conversation_id,
                    trace_id=trace_id,
                )
            except AppException as exc:
                set_span_status_error()
                yield {
                    "event": "error",
                    "data": {
                        "code": exc.code,
                        "message": redact_sensitive_text(exc.message),
                        "trace_id": trace_id,
                    },
                }
                return
            except Exception:
                set_span_status_error()
                yield {
                    "event": "error",
                    "data": {
                        "code": "AGENT_STREAM_FAILED",
                        "message": "The AI customer service request could not be completed.",
                        "trace_id": trace_id,
                    },
                }
                return
            finally:
                if context_tokens is not None:
                    reset_business_context(context_tokens)

        self._record_exchange(
            actor=actor,
            conversation_id=conversation_id,
            user_message=message,
            response=response,
        )
        yield {"event": "result", "data": response.model_dump(mode="json")}
        yield {"event": "done", "data": {"trace_id": trace_id}}

    def decide_ticket_confirmation(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        confirmation_id: str,
        approved: bool,
    ) -> ConsoleAgentResponse:
        thread_id = self._thread_id(actor, conversation_id)
        snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
        if not _has_pending_ticket_confirmation_next(snapshot):
            raise AppException(
                code="TICKET_CONFIRMATION_NOT_FOUND",
                message="There is no pending ticket confirmation for this conversation.",
                status_code=409,
            )

        fields = _pending_confirmation_fields(snapshot)
        if fields is None:
            raise AppException(
                code="TICKET_CONFIRMATION_NOT_FOUND",
                message="The pending ticket confirmation is no longer available.",
                status_code=409,
            )
        expected_confirmation_id = build_pending_ticket_confirmation(fields)["confirmation_id"]
        if confirmation_id.strip() != expected_confirmation_id:
            raise AppException(
                code="TICKET_CONFIRMATION_MISMATCH",
                message="The confirmation does not belong to this conversation.",
                status_code=409,
            )

        # The reliable discriminator lives in the confirmation interrupt
        # payload (written by the worker graph where refund_request_active /
        # cancel_request_active are visible): the top-level supervisor
        # snapshot.values never receives the worker flag, and the draft fields
        # alone are identical for both paths.
        is_refund_execution = self._snapshot_confirmation_is_refund_execution(
            snapshot
        )
        is_cancel_execution = self._snapshot_confirmation_is_cancel_execution(
            snapshot
        )

        tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
        try:
            if approved and self.settings.agent_mcp_tools_enabled:
                # Only the MCP path needs the confirmation pre-registered in the
                # shared store: the standalone MCP server re-checks it before
                # calling Java. The direct-Java path is idempotency-keyed at the
                # Java service instead, so registering here would be a dead write.
                from app.agents.mcp_tool_adapters import register_ticket_confirmation

                register_ticket_confirmation(
                    actor_id=actor.user_id,
                    fields=fields,
                    settings=self.settings,
                    is_refund_execution=is_refund_execution,
                    is_cancel_execution=is_cancel_execution,
                )
            state = resume_ticket_confirmation_interrupt(
                self.graph,
                thread_id=thread_id,
                approved=approved,
                actor_id=actor.user_id,
            )
        finally:
            reset_business_context(tokens)
        response = self._to_response(state, conversation_id=conversation_id)
        if is_cancel_execution:
            decision_copy = "确认取消订单" if approved else "取消取消"
        elif is_refund_execution:
            decision_copy = "确认退款" if approved else "取消退款"
        else:
            decision_copy = "确认创建工单" if approved else "取消创建工单"
        self._record_exchange(
            actor=actor,
            conversation_id=conversation_id,
            user_message=decision_copy,
            response=response,
        )
        return response

    def correct_ticket_confirmation(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        confirmation_id: str,
        ticket_fields: ConsoleAgentTicketFields,
    ) -> ConsoleAgentResponse:
        thread_id = self._thread_id(actor, conversation_id)
        self._require_pending_confirmation(thread_id, confirmation_id)
        snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
        is_refund_execution = self._snapshot_confirmation_is_refund_execution(
            snapshot
        )
        is_cancel_execution = self._snapshot_confirmation_is_cancel_execution(
            snapshot
        )
        corrected_fields = self._validate_corrected_ticket_fields(ticket_fields)
        tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
        try:
            state = resume_ticket_confirmation_interrupt(
                self.graph,
                thread_id=thread_id,
                approved=False,
                actor_id=actor.user_id,
                corrected_fields=corrected_fields,
            )
        finally:
            reset_business_context(tokens)
        response = self._to_response(state, conversation_id=conversation_id)
        if is_cancel_execution:
            correction_copy = "修改取消信息并重新确认"
        elif is_refund_execution:
            correction_copy = "修改退款信息并重新确认"
        else:
            correction_copy = "修改工单草稿并重新确认"
        self._record_exchange(
            actor=actor,
            conversation_id=conversation_id,
            user_message=correction_copy,
            response=response,
        )
        return response

    def request_human_handoff(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
    ) -> ConsoleAgentResponse:
        thread_id = self._thread_id(actor, conversation_id)
        self._reject_if_confirmation_is_pending(thread_id)
        snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
        state = dict(snapshot.values)
        handoff = self._human_handoff_from_state(state)
        if handoff is None:
            raise AppException(
                code="HUMAN_HANDOFF_NOT_AVAILABLE",
                message="当前会话暂不需要转交人工客服处理。",
                status_code=409,
            )

        order_hint = f"订单 {handoff.related_order_id} 的" if handoff.related_order_id else ""
        tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
        try:
            handoff_state = run_ticket_agent_in_thread(
                self.graph,
                f"请将{order_hint}问题转交人工客服处理。",
                thread_id=thread_id,
                actor_id=actor.user_id,
            )
        finally:
            reset_business_context(tokens)
        response = self._to_response(handoff_state, conversation_id=conversation_id)
        self._record_exchange(
            actor=actor,
            conversation_id=conversation_id,
            user_message="请求转人工客服处理",
            response=response,
        )
        return response

    def list_conversations(
        self,
        *,
        actor: ConsoleAgentActor,
        limit: int,
    ) -> list[ConsoleAgentConversationSummary]:
        try:
            return self.conversation_store.list_recent(actor=actor, limit=limit)
        except RedisError as exc:
            raise AppException(
                code="AGENT_CONVERSATION_STORE_UNAVAILABLE",
                message="会话记录服务暂时不可用，请稍后重试。",
                status_code=503,
            ) from exc

    def get_conversation(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
    ) -> ConsoleAgentConversation | None:
        try:
            return self.conversation_store.get(actor=actor, conversation_id=conversation_id)
        except RedisError as exc:
            raise AppException(
                code="AGENT_CONVERSATION_STORE_UNAVAILABLE",
                message="会话记录服务暂时不可用，请稍后重试。",
                status_code=503,
            ) from exc

    def submit_feedback(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        request: ConsoleAgentFeedbackRequest,
    ) -> ConsoleAgentFeedbackResponse:
        conversation = self.get_conversation(actor=actor, conversation_id=conversation_id)
        if conversation is None:
            raise AppException(
                code="AGENT_CONVERSATION_NOT_FOUND",
                message="The conversation does not exist, has expired, or is not available to this account.",
                status_code=404,
            )
        target = next(
            (
                item
                for item in reversed(conversation.messages)
                if item.role == "assistant" and item.trace_id == request.trace_id
            ),
            None,
        )
        if target is None:
            raise AppException(
                code="AGENT_RESPONSE_NOT_FOUND",
                message="The selected AI response does not belong to this conversation.",
                status_code=404,
            )
        target_index = conversation.messages.index(target)
        user_message = next(
            (
                item.content
                for item in reversed(conversation.messages[:target_index])
                if item.role == "user"
            ),
            None,
        )

        tokens = set_business_context(user_id=actor.user_id, tenant_id=actor.tenant_id)
        try:
            receipt = self.feedback_client.submit(
                conversation_id=conversation_id,
                trace_id=request.trace_id,
                rating=request.rating,
                reason=request.reason,
                agent_route=target.route or self._route_for_feedback(target),
                citation_count=len(target.citations),
                human_handoff_suggested=target.human_handoff is not None,
                user_message_excerpt=user_message,
                assistant_answer_excerpt=target.content,
                citation_summary_json=json.dumps(
                    [
                        {"source": citation.source, "title": citation.title, "chunk_id": citation.chunk_id}
                        for citation in target.citations[:10]
                    ],
                    ensure_ascii=False,
                ),
            )
        finally:
            reset_business_context(tokens)
        try:
            self.conversation_store.set_assistant_feedback(
                actor=actor,
                conversation_id=conversation_id,
                trace_id=request.trace_id,
                rating=receipt.rating,
                reason=receipt.reason,
            )
        except RedisError:
            logger.warning(
                "console_agent_feedback_transcript_update_failed conversation_id=%s actor_id=%s",
                conversation_id,
                actor.user_id,
            )
        return ConsoleAgentFeedbackResponse(
            feedback_id=receipt.feedback_id,
            rating=receipt.rating,
            reason=receipt.reason,
        )

    @staticmethod
    def _route_for_feedback(message: Any) -> str:
        if message.pending_ticket_confirmation is not None:
            return "ticket_confirmation"
        if message.created_ticket is not None:
            return "ticket_creation"
        if message.human_handoff is not None:
            return "human_handoff"
        if message.citations:
            return "policy_rag"
        return "agent"

    def _require_pending_confirmation(
        self,
        thread_id: str,
        confirmation_id: str,
    ) -> None:
        snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
        if not _has_pending_ticket_confirmation_next(snapshot):
            raise AppException(
                code="TICKET_CONFIRMATION_NOT_FOUND",
                message="There is no pending ticket confirmation for this conversation.",
                status_code=409,
            )

        fields = _pending_confirmation_fields(snapshot)
        if fields is None:
            raise AppException(
                code="TICKET_CONFIRMATION_NOT_FOUND",
                message="The pending ticket confirmation is no longer available.",
                status_code=409,
            )
        expected_confirmation_id = build_pending_ticket_confirmation(fields)["confirmation_id"]
        if confirmation_id.strip() != expected_confirmation_id:
            raise AppException(
                code="TICKET_CONFIRMATION_MISMATCH",
                message="The confirmation does not belong to this conversation.",
                status_code=409,
            )

    def _validate_corrected_ticket_fields(
        self,
        ticket_fields: ConsoleAgentTicketFields,
    ) -> TicketFields:
        fields = LLMTicketFields.model_validate(ticket_fields.model_dump()).model_dump()
        missing_fields = find_missing_ticket_fields(fields)
        if missing_fields:
            raise AppException(
                code="TICKET_FIELDS_INCOMPLETE",
                message="The corrected ticket fields are incomplete.",
                status_code=422,
            )
        return fields

    def _reject_if_confirmation_is_pending(self, thread_id: str) -> None:
        snapshot = self.graph.get_state(build_ticket_agent_thread_config(thread_id))
        if _has_pending_ticket_confirmation_next(snapshot):
            raise AppException(
                code="TICKET_CONFIRMATION_PENDING",
                message="Please confirm or cancel the pending ticket before sending a new message.",
                status_code=409,
            )

    def _thread_id(self, actor: ConsoleAgentActor, conversation_id: str) -> str:
        return f"console-{actor.tenant_id}-{actor.user_id}-{conversation_id}"

    def _to_response(
        self,
        state: dict[str, Any],
        *,
        conversation_id: str,
        trace_id: str | None = None,
    ) -> ConsoleAgentResponse:
        pending_confirmation = self._pending_confirmation_from_state(state)
        reply = (
            self._pending_confirmation_message(state, pending_confirmation)
            if pending_confirmation is not None
            else str(state.get("final_answer") or "The AI service did not return a usable reply.")
        )
        created_ticket = self._created_ticket_from_state(state)
        route = str(state.get("intent") or ("ticket_confirmation" if pending_confirmation else "agent"))
        citations = state.get("rag_citations") if isinstance(state.get("rag_citations"), list) else []
        suggestions = state.get("rag_suggestions") if isinstance(state.get("rag_suggestions"), list) else []
        human_handoff = (
            None
            if pending_confirmation is not None
            else self._human_handoff_from_state(state)
        )
        return ConsoleAgentResponse(
            reply=redact_sensitive_text(reply),
            conversation_id=conversation_id,
            trace_id=trace_id or get_trace_id(),
            route=route,
            citations=citations,
            suggestions=[str(item) for item in suggestions],
            pending_ticket_confirmation=pending_confirmation,
            created_ticket=created_ticket,
            human_handoff=human_handoff,
        )

    def _human_handoff_from_state(
        self,
        state: dict[str, Any],
    ) -> ConsoleAgentHumanHandoff | None:
        if (
            state.get("order_query_status") != "failed"
            or state.get("order_query_error_action") != "contact_human_support"
            or state.get("order_query_error_code") in HUMAN_HANDOFF_BLOCKED_ORDER_ERROR_CODES
        ):
            return None
        order_id = state.get("order_query_order_id")
        return ConsoleAgentHumanHandoff(
            reason="订单信息暂时无法可靠处理，建议由人工客服继续跟进。",
            related_order_id=str(order_id) if isinstance(order_id, str) and order_id.strip() else None,
        )

    def _record_exchange(
        self,
        *,
        actor: ConsoleAgentActor,
        conversation_id: str,
        user_message: str,
        response: ConsoleAgentResponse,
    ) -> None:
        try:
            self.conversation_store.append_exchange(
                actor=actor,
                conversation_id=conversation_id,
                user_message=user_message,
                response=response,
            )
        except RedisError:
            logger.warning(
                "console_agent_conversation_persist_failed conversation_id=%s actor_id=%s",
                conversation_id,
                actor.user_id,
            )

    def _snapshot_confirmation_is_refund_execution(self, snapshot: Any) -> bool:
        """Whether the pending confirmation interrupt is a refund execution.

        The flag is written into the interrupt payload by the worker graph
        (where refund_request_active is visible).  The top-level supervisor
        snapshot.values never carries the worker flag, so the interrupt payload
        is the only reliable source for both single- and multi-agent graphs.
        """
        for interrupt in getattr(snapshot, "interrupts", ()) or ():
            value = getattr(interrupt, "value", None)
            if (
                isinstance(value, dict)
                and value.get("kind") == TICKET_CONFIRMATION_INTERRUPT_KIND
            ):
                return value.get("is_refund_execution") is True
        return False

    def _snapshot_confirmation_is_cancel_execution(self, snapshot: Any) -> bool:
        """Whether the pending confirmation interrupt is a cancel execution.

        The flag is written into the interrupt payload by the worker graph
        (where cancel_request_active is visible).  The top-level supervisor
        snapshot.values never carries the worker flag, so the interrupt payload
        is the only reliable source for both single- and multi-agent graphs.
        """
        for interrupt in getattr(snapshot, "interrupts", ()) or ():
            value = getattr(interrupt, "value", None)
            if (
                isinstance(value, dict)
                and value.get("kind") == TICKET_CONFIRMATION_INTERRUPT_KIND
            ):
                return value.get("is_cancel_execution") is True
        return False

    def _pending_confirmation_from_state(
        self,
        state: dict[str, Any],
    ) -> ConsoleAgentTicketConfirmation | None:
        # The graph keeps the original draft after a decision for audit and
        # idempotency.  Only an active interrupt represents a confirmation the
        # user can still act on.
        if not state.get("__interrupt__"):
            return None

        interrupt_payload = get_ticket_confirmation_interrupt_payload(state)
        pending = interrupt_payload.get("pending_ticket_confirmation")
        if not isinstance(pending, dict):
            return None
        return ConsoleAgentTicketConfirmation.model_validate(
            {
                "confirmation_id": pending.get("confirmation_id"),
                "title": pending.get("title"),
                "summary": pending.get("summary"),
                "is_refund_execution": (
                    interrupt_payload.get("is_refund_execution") is True
                ),
                "is_cancel_execution": (
                    interrupt_payload.get("is_cancel_execution") is True
                ),
                "ticket_fields": pending.get("ticket_fields"),
            }
        )

    def _pending_confirmation_message(
        self,
        state: dict[str, Any],
        pending_confirmation: ConsoleAgentTicketConfirmation,
    ) -> str:
        interrupt_payload = None
        if state.get("__interrupt__"):
            interrupt_payload = get_ticket_confirmation_interrupt_payload(state)
        message = (
            interrupt_payload.get("message")
            if isinstance(interrupt_payload, dict)
            else state.get("ticket_confirmation_message")
        )
        return str(message or pending_confirmation.summary)

    def _created_ticket_from_state(self, state: dict[str, Any]) -> CreatedTicket | None:
        created_ticket = state.get("created_ticket")
        if not isinstance(created_ticket, dict):
            return None
        return CreatedTicket.model_validate(created_ticket)
