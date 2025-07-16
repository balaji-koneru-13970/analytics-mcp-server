from config import get_analytics_client_instance
import os
from fastmcp import Context
import math
import json

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
            Too many workspaces found. Please refine your search criteria or use the contains_str parameter to filter workspaces.
            The more characters you provide, the more accurate the results will be.
            """
        workspace["owned"] = owned_flag
        filtered.append(workspace)
        count += 1
    return filtered


VIEW_RESULT_LIMIT = os.getenv("ANALYTICS_VIEW_LIST_RESULT_SIZE") or 10
def get_views(org_id, workspace_id, allowedViewTypesIds, contains_str, from_relevant_views_tool=False):
    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    config={
        "viewTypes": allowedViewTypesIds or [0, 6],
        "noOfResult": VIEW_RESULT_LIMIT + 1,
        "sortedOrder": 0,
        "sortedColumn": 0,
        'startIndex': 1
    }
    if from_relevant_views_tool:
        config = {
            "viewTypes": allowedViewTypesIds or [0, 6]
        }
    if contains_str:
        config["keyword"] = contains_str
    view_list = workspace.get_views(config)
    if view_list is None or len(view_list) == 0:
        return "No views found"
    
    if not from_relevant_views_tool and len(view_list) > VIEW_RESULT_LIMIT:
        return """
        Too many views found. 
        Please refine your search criteria to use contains_str parameter to filter views if view name is provided.
        (or)
        Use the get_relevant_views() tool to get relevant views based on user query.
        """
    return view_list
        
    