from mcp.server.fastmcp import FastMCP
from tools.jira_service import JiraService
import os
import uvicorn
from mcp.server.fastmcp.server import TransportSecuritySettings
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.routing import Mount

jira = JiraService()

## Initialize MCP server

mcp = FastMCP(
    "Release-Manager",
    stateless_http=True,
    # This disables the Host header check that causes the 421 error
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)
)

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

# Create the final app that Uvicorn will run
# We mount the MCP sse_app at the root ('') to ensure /sse is top-level
# 3. Explicitly define the routes for Starlette
# This ensures they are visible to Uvicorn and Lambda immediately
app = Starlette(
    routes=[
        Route("/sse", endpoint=mcp.sse_app(), methods=["GET"]),
        Route("/messages", endpoint=mcp.sse_app(), methods=["POST"]),
    ]
)

if __name__ == "__main__":
    # Use "stdio" for local dev (VS Code) or "sse" for AWS deployment
    #mcp.run(transport="stdio")
    #port = int(os.environ.get("PORT", 8080))
    # CHANGE 127.0.0.1 to 0.0.0.0
    #mcp.run(transport="sse")
    # 1. Get the underlying ASGI app from FastMCP
    # For SSE transport, we use .sse_app()
    #app = mcp.sse_app()
   # main_app = FastAPI()

    # 3. Mount the MCP server to the /mcp path
    # This makes the routes: /mcp/sse and /mcp/messages
    #main_app.mount("/mcp", mcp.sse_app())
    
    # 2. Get port from environment (Lambda/Docker default is often 8080)
    #port = int(os.environ.get("PORT", 8080))
    
    # 3. Run with Uvicorn
    #uvicorn.run(main_app, host="0.0.0.0", port=port)

    port = int(os.environ.get("PORT", 8080))
    # Log the routes on startup so you can see them in CloudWatch
    print("Registered Routes:")
    for route in app.routes:
        print(f" -> {route.path} [{route.methods}]")
        
    uvicorn.run(app, host="0.0.0.0", port=port,proxy_headers=True, forwarded_allow_ips="*")
