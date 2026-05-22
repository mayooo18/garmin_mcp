import os
import json
from pathlib import Path
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from mcp.server.sse import SseServerTransport
import uvicorn

load_dotenv()

# Write Garmin tokens from environment variable to filesystem
# This allows Render to authenticate without interactive MFA
garmin_tokens = os.environ.get("GARMIN_TOKENS")
if garmin_tokens:
    token_dir = Path.home() / ".garminconnect"
    token_dir.mkdir(parents=True, exist_ok=True)
    token_file = token_dir / "garmin_tokens.json"
    token_file.write_text(garmin_tokens)
    print("Garmin tokens written to filesystem.")

# Load garmin_mcp's server then register your custom tools on top
from garmin_mcp.server import mcp as garmin_server
from custom.registry import register_custom_tools

register_custom_tools(garmin_server)

MCP_API_KEY = os.environ.get("MCP_API_KEY", "")

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_API_KEY and request.headers.get("X-API-Key") != MCP_API_KEY:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)

transport = SseServerTransport("/sse")
app = Starlette(routes=[Route("/sse", transport.handle_sse)])
app.add_middleware(APIKeyMiddleware)
transport.attach(garmin_server, app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))