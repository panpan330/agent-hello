# 阶段 7 第 9 节手动验证清单

本节是省 token 模式。自动化测试我已经覆盖核心错误映射；你手动验证时只需要确认关键场景即可。

## 1. 本节是否需要打开虚拟机

默认不需要。

本节主要改 Python AI 服务里的 Java 错误码映射逻辑：

```text
projects/ai-service/app/services/java_error_mapping.py
```

如果只是跑单元测试：

```text
不用打开 VMware Ubuntu
不用打开 Qdrant
不用打开 Milvus
不用打开 Redis
不用真实调用大模型
```

## 2. 推荐你手动跑的 Python 测试

进入 ai-service：

```powershell
cd D:\wendang\java+python+ai\projects\ai-service
```

运行：

```powershell
uv run pytest tests/test_java_error_mapping.py tests/test_java_order_client.py tests/test_java_ticket_client.py
```

期望结果：

```text
22 passed
```

## 3. 可选：验证订单查询错误映射

如果你想自己看测试细节，可以重点打开：

```text
tests/test_java_order_client.py
```

重点看这几个测试：

```text
test_java_order_client_maps_404_to_order_not_found
test_java_order_client_maps_access_denied_to_safe_user_message
test_java_order_client_hides_internal_auth_failure
```

你要理解的结果：

```text
ORDER_NOT_FOUND -> 订单不存在，请确认订单号是否正确。
ORDER_ACCESS_DENIED -> 当前账号无权查看或操作该订单。
INTERNAL_AUTH_FAILED -> 订单查询服务暂时不可用，请稍后重试。
```

## 4. 可选：验证工单创建错误映射

重点看：

```text
tests/test_java_ticket_client.py
```

重点测试：

```text
test_java_ticket_client_maps_order_not_support_ticket_to_user_safe_error
test_java_ticket_client_maps_idempotency_conflict_to_reconfirm_message
```

你要理解的结果：

```text
ORDER_NOT_SUPPORT_TICKET -> 当前订单暂不支持创建这类工单，如需帮助可以联系人工客服。
IDEMPOTENCY_KEY_CONFLICT -> 本次提交和已确认的工单请求不一致，请重新确认后再提交。
```

## 5. 可选：验证内部错误不会泄露

重点看：

```text
tests/test_java_error_mapping.py
```

重点测试：

```text
test_build_java_error_app_exception_hides_internal_auth_failure
```

你要确认：

```text
Java code 是 INTERNAL_AUTH_FAILED
Python 对外 code 是 TOOL_UPSTREAM_ERROR
Python message 里不出现“鉴权”
```

## 6. 你需要贴给我的结果

如果你手动跑了测试，把下面内容贴给我即可：

```text
uv run pytest tests/test_java_error_mapping.py tests/test_java_order_client.py tests/test_java_ticket_client.py
```

以及最后一行：

```text
22 passed
```

如果失败，把失败测试名和 assertion error 贴出来，不需要贴完整大段日志。
