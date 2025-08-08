import os
from AnalyticsClient import AnalyticsClient
from ZA_Config import ZA_Config

# Need to use pydantic to add validation
class Config:
    CLIENT_ID = os.getenv("ANALYTICS_CLIENT_ID")
    CLIENT_SECRET = os.getenv("ANALYTICS_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("ANALYTICS_REFRESH_TOKEN")
    ORG_ID = os.getenv("ANALYTICS_ORG_ID")
    MCP_DATA_DIR = os.getenv("ANALYTICS_MCP_DATA_DIR")
    ACCOUNTS_SERVER_URL = os.getenv("ACCOUNTS_SERVER_URL", "https://accounts.zoho.com")
    ANALYTICS_SERVER_URL = os.getenv("ANALYTICS_SERVER_URL", "https://analyticsapi.zoho.com")
    IS_ONPREMISE = os.getenv("IS_ONPREMISE", "false").lower() == "true"


analytics_client: AnalyticsClient  = None
def get_analytics_client_instance() -> AnalyticsClient:
    """
    Returns a singleton instance of the AnalyticsClient configured for the proper data center.
    Handling for multi-threaded environments is not required since each client will initaite a completely new
    process.
    """
    global analytics_client
    if not analytics_client:
        analytics_client = AnalyticsClient(Config.CLIENT_ID, Config.CLIENT_SECRET, Config.REFRESH_TOKEN)
        if Config.ACCOUNTS_SERVER_URL is None or Config.ANALYTICS_SERVER_URL is None:
            raise RuntimeError(
                f"ACCOUNTS_SERVER_URL (or) ANALYTICS_SERVER_URL environment variable is not set. "
                f"Please set it to your {Config.PRODUCT_NAME} accounts server URL and analytics server URL respectively."
            )
        analytics_client.accounts_server_url = Config.ACCOUNTS_SERVER_URL
        analytics_client.analytics_server_url = Config.ANALYTICS_SERVER_URL

        analytics_client.exclude_ssl = True if Config.IS_ONPREMISE else False
        analytics_client.user_agent = ZA_Config.USER_AGENT_NAME
    return analytics_client