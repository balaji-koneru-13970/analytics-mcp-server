from mcp_instance import mcp
from config import Config, get_analytics_client_instance
import os
import json
import urllib
import requests
import pandas as pd
from utils.common import retry_with_fallback
from utils.data_utils import import_data_implementation, export_view_implementation, query_data_implementation
import traceback
from fastmcp.server.dependencies import get_context
from utils.decorators import with_dynamic_doc



@mcp.tool()
@with_dynamic_doc("""
    <use_case>
    1. Analyzes the structure of a file (CSV or JSON) to determine its columns and data types.
    2. This can be used to understand the structure of a file before importing it into {PRODUCT_NAME}.
    3. If the table does not already exist and a file needs to be imported, this tool can be used to analyze the file structure and create a new table with the appropriate columns. 
    </use_case>

    <important_notes>
    - This tool supports only local files. If the file is a remote URL, download it first using the download_file tool.
    - The returned data types will not be the exact data types used in {PRODUCT_NAME}, but rather a general representation of the data types in Python.
    </important_notes>

    <arguments>
        file_path (str): The path to the local file to be analyzed.
    </arguments>

    <returns>
        A dictionary containing the column names and their respective data types.
    </returns>
""")
async def analyze_file_structure(file_path: str) -> dict:

    try:
        if not os.path.exists(file_path):
            return file_path + " does not exist. Please provide a valid file path."

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            structure = {col: str(df[col].dtype) for col in df.columns}
            return structure
        
        elif file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            

            if isinstance(json_data, list) and len(json_data) > 0:

                first_object = json_data[0]
                structure = {}
                
                for column, value in first_object.items():
                    if isinstance(value, int):
                        structure[column] = 'NUMBER'
                    elif isinstance(value, float):
                        structure[column] = 'DECIMAL'
                    elif isinstance(value, bool):
                        structure[column] = 'BOOLEAN'
                    else:
                        structure[column] = 'TEXT'
                
                return structure
            else:
                return "Invalid JSON format. Expected a list of objects."
        
        else:
            return "Unsupported file type. Please provide a CSV or JSON file."
    
    except Exception as e:
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while analyzing the file structure: {e}"

@mcp.tool()
@with_dynamic_doc("""
    <use_case>
    1. Downloads a file from a given URL and saves it to a local directory.
    2. This can be used to download files that need to be imported into {PRODUCT_NAME}.
    </use_case>

    <arguments>
        file_url (str): The URL of the file to be downloaded.
    </arguments>

    <returns>
        A string indicating the path where the file has been saved locally.
    </returns>
""")
async def download_file(file_url: str) -> str:

    try:

        download_dir = Config.MCP_DATA_DIR
        os.makedirs(download_dir, exist_ok=True)

        filename = os.path.basename(urllib.parse.urlparse(file_url).path)
        file_type = file_url.split('.')[-1].lower()
        if not filename:
            filename = f"downloaded_file.{file_type}"

        downloaded_path = os.path.join(download_dir, filename)

        # Get SSL verification setting from analytics client
        analytics_client = get_analytics_client_instance()
        verify_ssl = not analytics_client.exclude_ssl

        response = requests.get(file_url, stream=True, verify=verify_ssl)
        response.raise_for_status()

        with open(downloaded_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return f"File downloaded successfully and saved to {downloaded_path}"
    
    except Exception as e:
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return "Failed to download the file. Please check the URL and try again. Please make sure the file is accessible and the URL is correct."

@mcp.tool()
async def import_data(workspace_id: str, table_id: str, data: list[dict] | None = None, file_path: str | None = None, file_type: str | None = None, org_id: str | None = None) -> str:
    """
    <use_case>
    1. Imports data into a specified table in a workspace. The data to be imported should be provided as a list of dictionaries or as a file path (only local file). If file_path is provided, the format of the file should also be provided (csv or json), else the data parameter will be used.
    2. This can be used for both file upload as well as direct data import into a table.
    </use_case>

    <important_notes>
    - Make sure the the table already exists in the workspace before importing data.
    - If no table exists, create a table first using the create_table tool before importing the data.
    - if the file_path is a remote URL, download the file using download_file tool before using this tool.
    - if the file_path is a remote URL and table does not exist, you can create a new table using the create_table tool, analyse the structure (column structure of the table) of the file using analyse_file_structure tool and then import the data.
    </important_notes>


    <arguments>
        workspace_id (str): The ID of the workspace containing the table.
        table_id (str): The ID of the table to which data will be added. It is None if the data needs to be added to a new table.
        data (str): The data to be added to the table in json format.
        file_path (str): The path to a local file containing data to be added to the table.
        file_type (str): The type of the file being imported ("csv", "json").
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>

    <returns>
        A string indicating the result of the import operation. If successful, it returns a success message; otherwise, it returns an error message.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", import_data_implementation, workspace_id=workspace_id, file_path=file_path, table_id=table_id, file_type=file_type, data=data)
    except Exception as e:
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while adding data to the table : {e}"


@mcp.tool()
@with_dynamic_doc("""
   <use_case>
        Export an object from the workspace in the specified format. These objects can be tables, charts, or dashboards.
    </use_case>

    <important_notes>
        Mostly prefer html for charts and dashboards, and csv for tables.
    </important_notes>
    
    <arguments>
        workspace_id (str): The ID of the workspace from which to export objects.
        view_id (str): The ID of the {PRODUCT_NAME} view to be exported. This can be a table, chart, or dashboard.
        response_file_format (str): The format in which to export the objects. Supported formats are ["csv","json","xml","xls","pdf","html","image"].
        response_file_path (str): The path where the exported file will be saved.
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    <arguments>               
""")
async def export_view(workspace_id: str, view_id: str, response_file_format: str, response_file_path: str, org_id: str | None = None) -> str:

    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", export_view_implementation, response_file_format=response_file_format, response_file_path=response_file_path, workspace_id=workspace_id, view_id=view_id)
    except Exception as e:
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while exporting the object : {e}"


@mcp.tool()
@with_dynamic_doc("""
    <use_case>
    1. Executes a SQL query on the specified workspace and returns the top 20 rows as results.
    2. This can be used to retrieve data from {PRODUCT_NAME} using custom SQL queries.
    3. Use this when user asks for any queries from the data in the workspace.
    4. Use this to gather insights from the data in the workspace and answer user queries.
    5. Can be used to answer natural language queries by analysing the result of the SQL query.
    </use_case>

    <important_notes>
    - Always try to provide a mysql compatible sql select query alone.
    - Try to optimize the query to return only the required data and minimize the amount of data returned.
    - If table or column names contain spaces or special characters, enclose them in double quotes (e.g., `"Column Name"`).
    - Do not use more than one level of nested sub-queries.
    - Instead of doing n queries, try to combine them into a single query using joins or unions or sub-queries, while ensuring the query remains efficient.
    </important_notes>

    <arguments>
        workspace_id (str): The ID of the workspace where the query will be executed.
        sql_query (str): The SQL query to be executed.
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>

    <returns>
        Result of the SQL query in a comma-separated (list of list) format of the top 20 rows alone, the first row contains the column names. 
        If an error occurs, returns an error message.
    </returns>
""")
async def query_data(workspace_id: str, sql_query: str, org_id: str | None = None) -> list[dict]:

    if not org_id:
        org_id = Config.ORG_ID
    try:
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", query_data_implementation, workspace_id=workspace_id, sql_query=sql_query)
    except Exception as e:
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while executing the query: {e}"