import asyncio

from mcp import Client

from app.mcp_servers.minimal_server import mcp


def test_minimal_mcp_server_exposes_tools() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {tool.name for tool in tools.tools}

            assert "echo" in tool_names
            assert "add" in tool_names
            assert "validate_ticket_draft" in tool_names
            assert "simulate_tool_error_handling" in tool_names
            assert "inspect_tool_security_boundary" in tool_names
            assert "query_order" in tool_names
            assert "create_ticket" in tool_names

    asyncio.run(run())


def test_minimal_mcp_server_can_call_add_tool() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            result = await client.call_tool("add", {"a": 7, "b": 5})

            assert result.is_error is False
            assert result.structured_content == {"result": 12}

    asyncio.run(run())


def test_minimal_mcp_server_can_read_resource() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            result = await client.read_resource("learning://hello/panpan")

            assert result.contents[0].text == (
                "Hello, panpan. This resource comes from ai-service minimal MCP server."
            )

    asyncio.run(run())


def test_minimal_mcp_server_lists_project_resources() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            resources = await client.list_resources()

        resource_uris = {str(resource.uri) for resource in resources.resources}
        assert "learning://project/readme" in resource_uris
        assert "learning://project/progress" in resource_uris
        assert "learning://project/java-ai-contract" in resource_uris
        assert "learning://project/stage8-plan" in resource_uris
        assert "learning://project/mcp-create-ticket-note" in resource_uris

    asyncio.run(run())


def test_minimal_mcp_server_reads_project_resource() -> None:
    async def run() -> None:
        async with Client(mcp) as client:
            result = await client.read_resource("learning://project/stage8-plan")

        assert "阶段 8" in result.contents[0].text
        assert "MCP" in result.contents[0].text
        assert result.contents[0].mime_type == "text/markdown"

    asyncio.run(run())
