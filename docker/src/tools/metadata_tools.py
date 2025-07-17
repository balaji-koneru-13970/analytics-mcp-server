from mcp_instance import mcp
from config import Config, get_analytics_client_instance
from utils.metadata_util import filter_and_limit_workspaces, get_views
import os
from utils.common import retry_with_fallback
from utils.decorators import with_dynamic_doc

WORKSPACE_RESULT_LIMIT = os.getenv("ANALYTICS_WORKSPACE_LIST_RESULT_SIZE") or 20

@mcp.tool()
def get_workspaces_list(include_shared_workspaces: bool, contains_str: str | None = None) -> list[dict]:
    """
    <use_case>
        1) Fetches the list of workspaces in the user's organization.
        2) Used in the scenario where the user needs to select a workspace for further operations.
    </use_case>

    <important_notes>
        1) Try to avoid setting include_shared_workspaces to True unless you specifically need to see shared workspaces.
        2) If you don't find a workspace from the owned workspaces, try setting include_shared_workspaces to True to see if the workspace is shared with you.
    </important_notes>

    <arguments>
        include_shared_workspaces (bool): If True, includes shared workspaces in the list.
        contains_str (str | None): Optional string to filter workspaces with a contains criteria.
    </arguments>

    <returns>
        A list of dictionaries, each representing a workspace with its details.
        If an error occurs, returns an error message.
    </returns>
    """
    try:
        analytics_client = get_analytics_client_instance()
        if not include_shared_workspaces:
            workspaces = analytics_client.get_owned_workspaces()
            return filter_and_limit_workspaces(workspaces, contains_str, owned_flag=True, limit=WORKSPACE_RESULT_LIMIT)
        else:
            workspaces = analytics_client.get_workspaces()
            owned_result = filter_and_limit_workspaces(
                workspaces.get("ownedWorkspaces", []), contains_str, owned_flag=True, limit=WORKSPACE_RESULT_LIMIT
            )
            
            if isinstance(owned_result, str):
                return owned_result
            
            shared_result = filter_and_limit_workspaces(
                workspaces.get("sharedWorkspaces", []), contains_str, owned_flag=False,
                limit=WORKSPACE_RESULT_LIMIT - len(owned_result)
            )
            if isinstance(shared_result, str):
                return shared_result
            
            return owned_result + shared_result
    except Exception as e:
        return f"An error occurred while fetching workspaces: {str(e)}"
    
@mcp.tool()
@with_dynamic_doc("""
    <use_case>
        1) Fetches the list of views within a specified workspace.
        2) Used when user needs to retrieve the list of tables or reports or dashboards (any type of view) from a workspace
    </use_case>

    <important_notes>
    - In {PRODUCT_NAME}, Organizations are the highest level of data segregation. Each organization can have multiple workspaces, and each workspace can contain various views (tables, reports, dashboards, etc.).
    - In {PRODUCT_NAME}, the term view can refer to different types of data representations or objects within a workspace. A view might be a table (raw data), a pivot table (summarized data), a query table (custom SQL logic), a report (visualization), or other related elements.
        Different types of views available in {PRODUCT_NAME} are:
        (view type_id, view_type_name)
        0 - Table: A standard table
        2 - Chart: A graphical representation of data
        3 - Pivot Table: A table that summarizes data in a multidimensional format
        4 - Summary View: A view that provides a simple tabular summary of your data with aggregate functions applied.
        6 - Query Table: A derived table created from a custom SQL query
        7 - Dashboard: A collection of visualizations and reports
        
    - allowedViewTypesIds is optional and unless specifically required, it is recommended to not use it to filter the views by view type IDs. If not filter is applied, it will return all the tables and query tables in the workspace.
    </important_notes>

    <arguments>
        workspace_id (str): The ID of the workspace for which to fetch the views.
        allowedViewTypesIds (list[int] | None): Optional. If not provided, will auto-select all supported view types [0, 2, 3, 4, 6, 7].
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>

    <returns>
        A list of dictionaries, each representing a view with its details.
        If an error occurs, returns an error message.
    </returns>
""")
def get_view_list(workspace_id: str, allowedViewTypesIds: list[int] | None = None, org_id: str | None = None) -> list[dict]:
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", get_views,workspace_id=workspace_id, allowedViewTypesIds=allowedViewTypesIds)
    except Exception as e:
        return f"An error occurred while fetching views: {str(e)}"
    

@mcp.tool()
def get_view_details(view_id: str) -> dict:
    """
    <use_case>
        1) Fetches the details of a specific view in a workspace.
        2) Use this when you need detailed information about a specific view, such as its structure, data, and properties. (In case of a table, it will return the columns and their data types, dashboards will return the charts and their properties, etc.)
    </use_case>

    <arguments>
        view_id (str): The ID of the view for which to fetch details.
    </arguments>

    <returns>
        A dictionary containing the details of the specified view.
        If an error occurs, returns an error message.
    </returns>
    """
    try:    
        analytics_client = get_analytics_client_instance()
        view_details = analytics_client.get_view_details(view_id, config={"withInvolvedMetaInfo": True})
        view_details.pop('orgId')
        view_details.pop('createdByZuId')
        view_details.pop('lastDesignModifiedByZuId')
        for column in view_details.get("columns", []):
            column.pop("dataTypeId")
            column.pop("columnIndex")
            column.pop("pkTableName")
            column.pop("pkColumnName")
            column.pop("formulaDisplayName")
            column.pop("defaultValue")
        return view_details
    except Exception as e:
        return f"An error occurred while fetching view details: {str(e)}"
