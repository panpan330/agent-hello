"""Minimal MCP server for learning the Python SDK basics."""

from typing import Any

from app.mcp_servers import order_tool
from app.mcp_servers.ticket_validation import (
    TicketCategory,
    TicketDescription,
    TicketPriority,
    TicketTitle,
    validate_ticket_draft_arguments,
)
from app.mcp_servers.tool_error_handling import (
    ToolErrorScenario,
    simulate_tool_error_response,
)
from app.mcp_servers.tool_security import (
    SecurityScenario,
    build_tool_security_decision,
)
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


@mcp.tool()
def validate_ticket_draft(
    title: TicketTitle,
    description: TicketDescription,
    category: TicketCategory,
    priority: TicketPriority = "normal",
) -> dict[str, Any]:
    """Validate a support ticket draft without creating a real ticket."""
    return validate_ticket_draft_arguments(
        title=title,
        description=description,
        category=category,
        priority=priority,
    )


@mcp.tool()
def simulate_tool_error_handling(scenario: ToolErrorScenario) -> dict[str, Any]:
    """Simulate safe MCP tool success, business errors, and system errors."""
    return simulate_tool_error_response(scenario)


@mcp.tool()
def inspect_tool_security_boundary(
    scenario: SecurityScenario,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Inspect MCP tool safety decisions without executing real business writes."""
    return build_tool_security_decision(
        scenario=scenario,
        user_confirmed=user_confirmed,
    )


@mcp.tool()
def query_order(order_id: order_tool.OrderId) -> dict[str, Any]:
    """Query a business order through the MCP learning adapter."""
    return order_tool.query_order_for_mcp(order_id)


@mcp.resource("learning://hello/{name}")
def hello_resource(name: str) -> str:
    """Return a greeting resource for a learner."""
    return f"Hello, {name}. This resource comes from ai-service minimal MCP server."


if __name__ == "__main__":
    mcp.run()
