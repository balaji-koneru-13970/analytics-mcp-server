from mcp_instance import mcp
from config import Config, get_analytics_client_instance
from utils.common import retry_with_fallback
from utils.row_utils import add_row_implementation, delete_rows_implementation, update_rows_implementation

@mcp.tool()
def add_row(workspace_id: str, table_id: str, columns: dict[str,str], org_id: str | None = None) -> dict:
    """
    <use_case>
    Adds a new row to the specified table.
    </use_case>

    <arguments>
    - workspace_id: The ID of the workspace where the table is located.
    - table_id: The ID of the table to which the row will be added.
    - columns: A dictionary containing the column names and their corresponding values for the new row.
    - org_id: The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID    
        retry_with_fallback([org_id], workspace_id, "WORKSPACE", add_row_implementation, workspace_id=workspace_id, table_id=table_id, columns=columns)
    except Exception as e:
        return {"Error while adding row": str(e)}
    return "Row added successfully."

@mcp.tool()
def delete_rows(workspace_id: str, table_id: str, criteria: str, org_id: str | None = None):
    """
    <use_case>
    - Deletes rows from the specified table based on the given criteria.
    </use_case>

    <arguments>
    - workspace_id: The ID of the workspace where the table is located.
    - table_id: The ID of the table from which rows will be deleted.
    - criteria: A string representing the criteria for selecting rows to delete.
        Example criteria: "\"SalesTable\".\"Region\"='East'"
    - org_id: The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
            
        retry_with_fallback([org_id], workspace_id, "WORKSPACE", delete_rows_implementation, workspace_id=workspace_id, table_id=table_id, criteria=criteria)
    except Exception as e:
        return {"Error while deleting rows: ": str(e)}
    return "Rows deleted successfully."

@mcp.tool()
def update_rows(workspace_id: str, table_id: str, columns: dict[str,str], criteria: str, org_id: str | None = None):
    """
    <use_case>
    Updates rows in the specified table based on the given criteria.
    </use_case>

    <arguments>
    - workspace_id: The ID of the workspace where the table is located.
    - table_id: The ID of the table to be updated.
    - columns: A dictionary containing the column names and their new values for the update.
    - criteria: A string representing the criteria for selecting rows to update.
        Example criteria: "\"SalesTable\".\"Region\"='East'"
    - org_id: The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
                        
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", update_rows_implementation, workspace_id=workspace_id, table_id=table_id, criteria=criteria, columns=columns)
    except Exception as e:
        return {"Error while updating rows: ": str(e)}