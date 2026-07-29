"""Minimal MCP server for learning the Python SDK basics."""

from typing import Any

from app.mcp_servers import order_tool, ticket_tool
from app.mcp_servers.project_resources import read_project_resource
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


@mcp.tool()
def create_ticket(
    requester_id: ticket_tool.RequesterId,
    title: ticket_tool.TicketTitle,
    description: ticket_tool.TicketDescription,
    category: ticket_tool.TicketCategory,
    confirmation_id: ticket_tool.ConfirmationId,
    priority: ticket_tool.TicketPriority = ticket_tool.TicketPriority.NORMAL,
    related_order_id: ticket_tool.RelatedOrderId = None,
    user_confirmed: bool = False,
) -> dict[str, Any]:
    """Create a support ticket after user confirmation and idempotency checks."""
    return ticket_tool.create_ticket_for_mcp(
        requester_id=requester_id,
        title=title,
        description=description,
        category=category,
        priority=priority,
        related_order_id=related_order_id,
        confirmation_id=confirmation_id,
        user_confirmed=user_confirmed,
    )


@mcp.resource("learning://hello/{name}")
def hello_resource(name: str) -> str:
    """Return a greeting resource for a learner."""
    return f"Hello, {name}. This resource comes from ai-service minimal MCP server."


@mcp.resource(
    "learning://project/readme",
    title="Project README",
    description="GitHub homepage and project learning entry.",
    mime_type="text/markdown",
)
def project_readme_resource() -> str:
    """Return the project README as MCP context."""
    return read_project_resource("learning://project/readme")


@mcp.resource(
    "learning://project/progress",
    title="Learning Progress",
    description="Current learning stage, lesson status, and roadmap progress.",
    mime_type="text/markdown",
)
def project_progress_resource() -> str:
    """Return the learning progress document as MCP context."""
    return read_project_resource("learning://project/progress")


@mcp.resource(
    "learning://project/java-ai-contract",
    title="Java AI API Contract",
    description="Contract between Python AI service and Java business service.",
    mime_type="text/markdown",
)
def java_ai_contract_resource() -> str:
    """Return the Java and AI API contract document as MCP context."""
    return read_project_resource("learning://project/java-ai-contract")


@mcp.resource(
    "learning://project/stage8-plan",
    title="Stage 8 MCP Learning Plan",
    description="Planned lessons for MCP and AI tool ecosystem basics.",
    mime_type="text/markdown",
)
def stage8_plan_resource() -> str:
    """Return the stage 8 MCP learning plan as MCP context."""
    return read_project_resource("learning://project/stage8-plan")


@mcp.resource(
    "learning://project/mcp-create-ticket-note",
    title="MCP Create Ticket Tool Note",
    description="Stage 8 lesson 16 note about wrapping create_ticket as an MCP tool.",
    mime_type="text/markdown",
)
def mcp_create_ticket_note_resource() -> str:
    """Return the latest completed MCP create_ticket lesson note."""
    return read_project_resource("learning://project/mcp-create-ticket-note")


if __name__ == "__main__":
    mcp.run()
