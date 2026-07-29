"""Minimal MCP server for learning the Python SDK basics."""

from mcp.server import MCPServer


mcp = MCPServer("ai-service-learning-mcp")


@mcp.tool()
def echo(message: str) -> str:
    """Return the same message back to the caller."""
    return message


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b


@mcp.resource("learning://hello/{name}")
def hello_resource(name: str) -> str:
    """Return a greeting resource for a learner."""
    return f"Hello, {name}. This resource comes from ai-service minimal MCP server."


if __name__ == "__main__":
    mcp.run()
