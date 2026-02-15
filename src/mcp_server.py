import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Route, Router, Mount
from starlette.responses import JSONResponse
from tools.jira_service import JiraService

jira = JiraService()

## Initialize MCP server

# 1. Initialize FastMCP with stateless_http=True
mcp = FastMCP(
    "Release-Manager",
    stateless_http=True,
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

app = mcp.streamable_http_app()

# 3. Add your custom Health Check route directly to the MCP app's router
@app.route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "ok"})

# 4. Add the HTTPS Middleware directly to the MCP app
@app.middleware("http")
async def trust_proxy_and_force_https(request, call_next):
    request.scope["scheme"] = "https"
    return await call_next(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print("--- STARTING MCP SERVER (Stateless HTTP) ---")
    
    # We run the 'app' (which is the MCP streamable app) directly.
    # The endpoint for the Inspector will now be the ROOT URL of your Lambda.
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
