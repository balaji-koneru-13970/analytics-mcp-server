import os
import configparser

class ZA_Config:
    """
    ZA_Config class to manage configuration settings for the application.
    It reads configuration from a properties file and allows access to various settings
    such as product name, version, and server name based on the active profile.
    """
    parser = configparser.ConfigParser()
    parser.read('config.properties')

    active_profile = os.environ.get('APP_PROFILE', 'ZA_CLOUD') # APP_PROFILE is the environment variable to set the active profile

    if active_profile not in parser:
        raise ValueError(f"[ERROR] Profile '{active_profile}' not found in config.properties")

    PRODUCT_NAME = parser.get(active_profile, 'PRODUCT_NAME')
    PRODUCT_VERSION = parser.get(active_profile, 'PRODUCT_VERSION')
    MCP_SERVER_NAME = parser.get(active_profile, 'MCP_SERVER_NAME')
