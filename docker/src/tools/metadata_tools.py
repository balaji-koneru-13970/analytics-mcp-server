from mcp_instance import mcp
from config import Config, get_analytics_client_instance
from utils.metadata_util import filter_and_limit_workspaces, get_views
import os
from utils.common import retry_with_fallback
from fastmcp import Context
from fastmcp.server.dependencies import get_context
import math
import json
import traceback

WORKSPACE_RESULT_LIMIT = os.getenv("ANALYTICS_WORKSPACE_LIST_RESULT_SIZE") or 20

@mcp.tool()
async def get_workspaces_list(include_shared_workspaces: bool, contains_str: str | None = None) -> list[dict]:
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
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while fetching workspaces: {str(e)}"
    

@mcp.tool()
async def get_view_details(view_id: str) -> dict:
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
        ctx = get_context()
        await ctx.error(traceback.format_exc())
        return f"An error occurred while fetching view details: {str(e)}"
    

@mcp.tool()
async def search_views(
    workspace_id: str, 
    natural_language_query: str | None = None,
    view_contains_str: str | None = None,
    allowedViewTypesIds: list[int] | None = None,
    org_id: str | None = None
) -> list[dict]:
    """
    <use_case>
        1) Searches for views in a workspace using either contains string name matching or natural language query via Retrieval-Augmented Generation (RAG).
        2) Use this when you need to find specific views or views relevant to a question.
    </use_case>

    <important_notes>
        - If view_contains_str is provided, performs simple string matching on view names.
        - If view_contains_str is None and natural_language_query is provided with ctx available, performs intelligent RAG-based search using natural language.
        - If both view_contains_str and natural_language_query are provided, view_contains_str takes precedence and RAG search is not performed.
        - If both are None, returns returns the views without filtering. If there are too many views, it will return an error message.
        - If not specified explicitly, use [0, 6] as default allowedViewTypesIds, which includes Table and Query Table.
    </important_notes>

    <arguments>
        - workspace_id (str): The ID of the workspace to search in.
        - natural_language_query (str | None): Natural language query for intelligent search. Ignored if view_contains_str is provided.
        - view_contains_str (str | None): String to filter views by name matching. Takes precedence over natural_language_query.
        - allowedViewTypesIds (list[int] | None): Optional list of view type IDs to filter results.
            Different types of views available in zoho analytics are:
            (view type_id, view_type_name)
            0 - Table: A standard table
            2 - Chart: A graphical representation of data
            3 - Pivot Table: A table that summarizes data in a multidimensional format
            4 - Summary View: A view that provides a simple tabular summary of your data with aggregate functions applied
            6 - Query Table: A derived table created from a custom SQL query
            7 - Dashboard: A collection of visualizations and reports
        - ctx (Context | None): Context for async operations - required for natural language search.
        - org_id (str | None): Organization ID. Defaults to config value if not provided.
    </arguments>

    <returns>
        A list of dictionaries representing matching views.
        If an error occurs, returns an error message.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID

        if (view_contains_str is not None and view_contains_str.strip() != "") or (natural_language_query is None or natural_language_query.strip() == ""):
            return retry_with_fallback([org_id], workspace_id, "WORKSPACE", get_views,workspace_id=workspace_id, allowedViewTypesIds=allowedViewTypesIds, contains_str=view_contains_str, from_relevant_views_tool=False)
    
        else:
            view_list = retry_with_fallback([org_id], workspace_id, "WORKSPACE",get_views,workspace_id=workspace_id, allowedViewTypesIds=[0, 6], contains_str=None, from_relevant_views_tool=True)
            if view_list is None or len(view_list) == 0:
                return "No views found in the workspace."
            

            # Prepare view data
            view_id_to_details = {}
            transformed_view_list = []
            for view in view_list:
                filtered_view = {k: v for k, v in view.items() if k in {"viewId", "viewName", "viewDesc"}}
                transformed_view_list.append(filtered_view)
                view_id_to_details[view["viewId"]] = filtered_view
            
            current_view_list = transformed_view_list
            batch_size = 15
            max_epochs = 5
            epoch = 1

            sample_supported = True

            # Epoch-based filtering
            ctx = get_context()
            while len(current_view_list) > 15 and epoch <= max_epochs and sample_supported:
                await ctx.info(f"Starting Epoch {epoch} with {len(current_view_list)} views")
                
                filtered_view_list = []
                number_of_batches = math.ceil(len(current_view_list) / batch_size)
                
                for batch_number in range(number_of_batches):
                    views_in_batch = current_view_list[batch_number * batch_size : (batch_number + 1) * batch_size]
                    
                    prompt = f"""
                    You are an expert at identifying and ranking relevant views (tables, reports, dashboards) based on natural language queries.
                    
                    EPOCH {epoch} - BATCH {batch_number + 1}/{number_of_batches}
                    Current views number in this epoch: {len(current_view_list)}
                    Views number in this batch: {len(views_in_batch)}
                    
                    Your task: Analyze the following views and rank them by relevance to the query. Return the TOP 5 MOST RELEVANT views from this batch based on your ranking.
                    
                    Views in this batch:
                    {views_in_batch}
                    
                    Natural language query: `{natural_language_query}`
                    
                    Instructions:
                    1. Rank ALL views in this batch by relevance to the query
                    2. Select the TOP 5 most relevant views based on your rankingk
                    3. If there are fewer than 5 views in the batch, return only the relevant views from them
                    4. Consider view names, descriptions, and how well they match the query intent
                    5. The output provided should be a properly escaped json and should not contain other formatting characters like new lines.
                    
                    Strictly provide your output in the following JSON format:
                    {{"relevant_views":[<list-of-top-5-view-ids-in-order-of-relevance>]}}
                    """

                    try:
                        response_string = await ctx.sample(prompt)
                    except Exception as e:
                        ctx.error(traceback.format_exc())
                        if batch_number == 0 and epoch == 1:
                            await ctx.info("Sampling is not supported in this environment")
                            sample_supported = False
                        break


                    if response_string.type != "text":
                        return "Error in processing the RAG response. Please try again."
                    
                    log_message = {
                        "epoch": epoch,
                        "batch": batch_number + 1,
                        "prompt": prompt,
                        "response": response_string.text,
                    }
                    await ctx.info(json.dumps(log_message, indent=2))

                    response_json = json.loads(response_string.text)

                    for view_id in response_json.get("relevant_views", []):
                        if view_id in view_id_to_details:
                            view_details = {
                                'viewId': view_id,
                                'viewName': view_id_to_details[view_id]['viewName'],
                                'viewDesc': view_id_to_details[view_id]['viewDesc']
                            }
                            filtered_view_list.append(view_details)
                

                if not sample_supported:
                    break

                await ctx.info(f"Epoch {epoch} completed. Reduced from {len(current_view_list)} to {len(filtered_view_list)} views")
                current_view_list = filtered_view_list
                epoch += 1

            if not sample_supported:
                await ctx.info("Using fallback mechanism: Returning first 20 views from the workspace")
                return transformed_view_list[:20]

            await ctx.info(f"Final result: {len(current_view_list)} views after {epoch - 1} epochs")
            return current_view_list


    
    except Exception as e:
        ctx.error(traceback.format_exc())
        return f"An error occurred while fetching views: {e}"