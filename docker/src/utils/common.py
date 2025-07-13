from config import get_analytics_client_instance

def retry_with_fallback(original_org_id, entity_id, entity_type, api_call, *args, **kwargs):
    if not isinstance(original_org_id, list):
        raise ValueError("original_id must be passed as a list to allow modification")
    try:
        return api_call(org_id=original_org_id[0], *args, **kwargs)
    except Exception as e:
        if hasattr(e, 'errorCode') and (e.errorCode == 8084 or e.errorCode == 7387):
            proper_org_id = get_proper_org_id(entity_id, entity_type)
            result = api_call(org_id=proper_org_id,  *args, **kwargs)
            original_org_id[0] = proper_org_id
            return result
        raise e

def get_proper_org_id(entity_id, entity_type):
    if entity_type == "WORKSPACE":
        return get_workspace_org_id(entity_id)
    elif entity_type == "VIEW":
        return get_view_org_id(entity_id)


def get_workspace_org_id(workspace_id):
    analytics_client = get_analytics_client_instance()
    workspace_details = analytics_client.get_workspace_details(workspace_id)
    return workspace_details.get("orgId")


def get_view_org_id(view_id):
    analytics_client = get_analytics_client_instance()
    view_details = analytics_client.get_view_details(view_id, config={"withInvolvedMetaInfo": False})
    return view_details.get("orgId")