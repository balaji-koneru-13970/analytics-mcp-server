from config import get_analytics_client_instance

def add_row_implementation(org_id, workspace_id, table_id, columns):
    analytics_client = get_analytics_client_instance()
    view = analytics_client.get_view_instance(org_id, workspace_id, table_id)
    return view.add_row(columns)

def update_rows_implementation(org_id, workspace_id, table_id, criteria, columns):
    analytics_client = get_analytics_client_instance()
    view = analytics_client.get_view_instance(org_id, workspace_id, table_id)
    result = view.update_row(columns, criteria)
    return "Rows updated successfully."

def delete_rows_implementation(org_id, workspace_id, table_id, criteria):
    analytics_client = get_analytics_client_instance()
    view = analytics_client.get_view_instance(org_id, workspace_id, table_id)
    return view.delete_row(criteria)