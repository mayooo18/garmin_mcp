import os
import sys
from dotenv import load_dotenv
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
import uvicorn

load_dotenv()

# Inject Garmin tokens from env var so garminconnect can load them directly.
# garminconnect reads GARMINTOKENS; if the value is >512 chars it calls
# client.loads() (in-memory) instead of trying to read from the filesystem.
garmin_tokens = os.environ.get("GARMIN_TOKENS") or os.environ.get("GARMINTOKENS")
if garmin_tokens:
    os.environ["GARMINTOKENS"] = garmin_tokens  # garminconnect's expected var name
    print("Garmin tokens loaded from environment.", file=sys.stderr)
else:
    print("No GARMIN_TOKENS env var found — will try ~/.garminconnect on disk.", file=sys.stderr)

# --- Garmin init (mirrors the logic in garmin_mcp/__init__.py) ---
from garmin_mcp import (
    init_api, email, password,
    activity_management, health_wellness, user_profile, devices,
    gear_management, weight_management, challenges, training,
    workouts, workout_templates, data_management, womens_health,
    nutrition, workout_builders, courses, activity_analysis,
)
from custom.registry import register_custom_tools

garmin_client = init_api(email, password)
if not garmin_client:
    print("Failed to initialize Garmin Connect client. Exiting.", file=sys.stderr)
    sys.exit(1)

# Configure every module with the authenticated client
activity_management.configure(garmin_client)
health_wellness.configure(garmin_client)
user_profile.configure(garmin_client)
devices.configure(garmin_client)
gear_management.configure(garmin_client)
weight_management.configure(garmin_client)
challenges.configure(garmin_client)
training.configure(garmin_client)
workouts.configure(garmin_client)
data_management.configure(garmin_client)
womens_health.configure(garmin_client)
nutrition.configure(garmin_client)
workout_builders.configure(garmin_client)
courses.configure(garmin_client)
activity_analysis.configure(garmin_client)

# --- Build the MCP server ---
PORT = int(os.environ.get("PORT", 8000))

mcp = FastMCP(
    "Garmin Fitness Assistant",
    host="0.0.0.0",
    port=PORT,
)

# Register all garmin_mcp tools
mcp = activity_management.register_tools(mcp)
mcp = health_wellness.register_tools(mcp)
mcp = user_profile.register_tools(mcp)
mcp = devices.register_tools(mcp)
mcp = gear_management.register_tools(mcp)
mcp = weight_management.register_tools(mcp)
mcp = challenges.register_tools(mcp)
mcp = training.register_tools(mcp)
mcp = workouts.register_tools(mcp)
mcp = data_management.register_tools(mcp)
mcp = womens_health.register_tools(mcp)
mcp = nutrition.register_tools(mcp)
mcp = workout_builders.register_tools(mcp)
mcp = courses.register_tools(mcp)
mcp = activity_analysis.register_tools(mcp)
mcp = workout_templates.register_resources(mcp)

# Register custom tools (profile, calories, recovery, marathon)
register_custom_tools(mcp)

# --- Optional API-key protection ---
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_API_KEY and request.headers.get("X-API-Key") != MCP_API_KEY:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return await call_next(request)


# Build Starlette app from FastMCP and attach middleware
app = mcp.sse_app()
if MCP_API_KEY:
    app.add_middleware(APIKeyMiddleware)

if __name__ == "__main__":
    print(f"Starting Garmin MCP SSE server on http://0.0.0.0:{PORT}/sse", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
