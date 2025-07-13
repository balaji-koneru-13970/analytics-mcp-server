from config import get_analytics_client_instance
import os

def filter_and_limit_workspaces(workspaces, contains_str, owned_flag, limit=20):
    """
    Utility to filter workspaces by name and limit the result count.
    Adds 'owned' flag to each workspace.
    """
    filtered = []
    count = 0
    for workspace in workspaces:
        if contains_str and contains_str.lower() not in workspace["workspaceName"].lower():
            continue
        if count >= limit:
            return """
            Too many workspaces found. Please refine your search criteria or use the startsWithStr parameter to filter workspaces.
            The more characters you provide, the more accurate the results will be.
            """
        workspace["owned"] = owned_flag
        filtered.append(workspace)
        count += 1
    return filtered


VIEW_RESULT_LIMIT = os.getenv("ANALYTICS_VIEW_LIST_RESULT_SIZE") or 30
def get_views(org_id, workspace_id, allowedViewTypesIds):
    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    return workspace.get_views(config={
        "viewTypes": allowedViewTypesIds or [0, 6],
        "noOfResult": VIEW_RESULT_LIMIT,
        "sortedOrder": 0,
        "sortedColumn": 0,
        'startIndex': 1
    })