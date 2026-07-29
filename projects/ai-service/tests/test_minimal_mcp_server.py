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
