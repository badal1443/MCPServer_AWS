from mcp.server.fastmcp import FastMCP
from tools.jira_service import JiraService
import os
import uvicorn

jira = JiraService()

## Initialize MCP server

mcp = FastMCP("Release Manager MCP server",stateless_http=True)

# Register your existing tools.

@mcp.tool()
def check_jira_ticket(ticket_id: str) -> dict:
    """Fetches status of a Jira ticket. Checks status of JIRA ticket"""
    #return f"Ticket {ticket_id} is currently 'In Progress'."
    return jira.get_release_summary(ticket_id)

@mcp.tool()
def Update_status_of_jira_ticket(ticket_id: str, status: str) -> dict:
    """Updates status of JIRA ticket."""
    # Update JIRA ticket status
    return jira.transition_release(ticket_id,status)

@mcp.tool()
def trigger_bitbucket_build(repo_name: str) -> dict:
    """Triggers a Bitbucket pipeline for the given repository."""
    # Insert your existing Bitbucket logic here
    return f"Pipeline started for {repo_name}."

if __name__ == "__main__":
    # Use "stdio" for local dev (VS Code) or "sse" for AWS deployment
    #mcp.run(transport="stdio")
    #port = int(os.environ.get("PORT", 8080))
    # CHANGE 127.0.0.1 to 0.0.0.0
    #mcp.run(transport="sse")
    # 1. Get the underlying ASGI app from FastMCP
    # For SSE transport, we use .sse_app()
    app = mcp.sse_app()
    
    # 2. Get port from environment (Lambda/Docker default is often 8080)
    port = int(os.environ.get("PORT", 8080))
    
    # 3. Run with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
