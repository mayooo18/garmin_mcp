from custom.profile.tools import (
    get_user_profile,
    save_user_preference,
    reset_user_profile,
)
from custom.logic.calories import recommend_daily_calories
from custom.logic.recovery import get_recovery_summary
from custom.logic.marathon import get_marathon_readiness


def register_custom_tools(mcp):
    """
    Registers all custom tools onto garmin_mcp's existing server instance.
    Call this once at startup before the server begins serving requests.
    """
    mcp.tool()(get_user_profile)
    mcp.tool()(save_user_preference)
    mcp.tool()(reset_user_profile)
    mcp.tool()(recommend_daily_calories)
    mcp.tool()(get_recovery_summary)
    mcp.tool()(get_marathon_readiness)