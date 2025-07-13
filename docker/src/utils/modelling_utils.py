from config import get_analytics_client_instance

def create_workspace_implementation(org_id, workspace_name):
    analytics_client = get_analytics_client_instance()
    org = analytics_client.get_org_instance(org_id)
    result = org.create_workspace(workspace_name)
    if result:
        return f"Workspace '{workspace_name}' created successfully. Workspace Id : {result}"


def create_table_implementation(org_id, workspace_id, table_name, columns_list):
    analytics_client = get_analytics_client_instance()
    table_design = {}
    table_design["TABLENAME"] = table_name
    table_design["COLUMNS"] = columns_list
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    table_id = workspace.create_table(table_design)
    return "Table created successfully. Table Id : " + str(table_id)


def create_aggregate_formula_implementation(org_id, workspace_id, table_id, expression, formula_name):
    analytics_client = get_analytics_client_instance()
    view = analytics_client.get_view_instance(org_id, workspace_id, table_id)
    result = view.add_aggregate_formula(formula_name, expression)
    return "Aggregate formula created successfully. Formula Id : " + str(result)


def create_chart_report_implementation(org_id, workspace_id, table_name, chart_name, chart_details, filters=None):
    if "chartType" not in chart_details:
        return "Chart type is required. Please provide 'chartType' in chart_details."

    chart_type = chart_details["chartType"]
    if chart_type not in ["bar", "line", "pie", "scatter", "bubble"]:
        return f"Invalid chart type. Allowed types: ['bar', 'line', 'pie', 'scatter', 'bubble']"

    x_axis = chart_details.get("x_axis")
    y_axis = chart_details.get("y_axis")
    if not x_axis or not y_axis:
        return "Both x_axis and y_axis must be provided in chart_details."

    for axis_name, axis in [("x_axis", x_axis), ("y_axis", y_axis)]:
        if "columnName" not in axis or "operation" not in axis:
            return f"{axis_name} must contain 'columnName' and 'operation'."

    if chart_type in ["bar", "line", "pie", "bubble"] and x_axis["operation"] in ["Measure", "sum", "average", "min", "max"]:
        return f"For chart type '{chart_type}', x_axis operation cannot be 'Measure', 'sum', 'average', 'min', or 'max'. Use 'dimension' instead."

    if chart_type in ["bar", "line", "pie", "bubble"] and y_axis["operation"] == "actual":
        return f"For chart type '{chart_type}', y_axis operation cannot be 'actual'. Use 'sum' instead."

    axis_columns = []
    for axis_type, axis in [("xAxis", x_axis), ("yAxis", y_axis)]:
        axis_config = {
            "type": axis_type,
            "columnName": axis["columnName"],
            "operation": axis["operation"]
        }
        if "tableName" in axis:
            axis_config["tableName"] = axis["tableName"]
        axis_columns.append(axis_config)

    config = {
        "baseTableName": table_name,
        "title": chart_name,
        "reportType": "chart",
        "chartType": chart_type,
        "axisColumns": axis_columns
    }

    if filters:
        if not isinstance(filters, list):
            return "Filters must be a list of dictionaries."
        for f in filters:
            if not {"columnName", "operation", "filterType", "values", "exclude"}.issubset(f):
                return "Each filter must contain 'columnName', 'operation', 'filterType', 'values', and 'exclude'."
        config["filters"] = filters

    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    report_id = workspace.create_report(config)
    return f"Chart report created successfully. Report ID: {report_id}"


def create_pivot_report_implementation(org_id, workspace_id, table_name, report_name, pivot_details, filters=None):
    if not pivot_details:
        return "Pivot details must be provided."

    if not any(key in pivot_details for key in ["row", "column", "data"]):
        return "At least one of 'row', 'column', or 'data' must be provided in pivot_details."

    axis_columns = []
    required_pivot_axis_keys = {"columnName", "tableName", "operation"}

    for axis_type, axis_key in [("row", "row"), ("column", "column"), ("data", "data")]:
        if axis_key in pivot_details:
            axis_list = pivot_details[axis_key]
            if not isinstance(axis_list, list) or not axis_list:
                return f"{axis_key} must be a non-empty list of dictionaries with 'columnName', 'tableName' and operations."

            for entry in axis_list:
                if not required_pivot_axis_keys.issubset(entry):
                    return f"Each entry in '{axis_key}' must contain 'columnName' and 'tableName' and 'operation'."
                
                if axis_type == "row" or axis_type == "column":
                    default_operation = "actual"
                else:
                    default_operation = "count"
                
                axis_columns.append({
                    "type": axis_type,
                    "columnName": entry["columnName"],
                    "operation": entry.get("operation", default_operation),
                    "tableName": entry["tableName"]
                })

    config = {
        "baseTableName": table_name,
        "title": report_name,
        "reportType": "pivot",
        "axisColumns": axis_columns
    }

    if filters:
        if not isinstance(filters, list):
            return "Filters must be a list of dictionaries."
        for f in filters:
            if not {"columnName", "operation", "filterType", "values", "exclude"}.issubset(f):
                return "Each filter must contain 'columnName', 'operation', 'filterType', 'values', and 'exclude'."
        config["filters"] = filters

    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    report_id = workspace.create_report(config)
    return f"Pivot report created successfully. Report ID: {report_id}"


def create_summary_report_implementation(org_id, workspace_id, table_name, report_name, summary_details, filters=None):
    if "group_by" not in summary_details or "aggregate" not in summary_details:
        return "Both 'group_by' and 'aggregate' must be provided in summary_details."

    group_by = summary_details["group_by"]
    aggregate = summary_details["aggregate"]

    if not isinstance(group_by, list) or not group_by:
        return "'group_by' must be a non-empty list."
    if not isinstance(aggregate, list) or not aggregate:
        return "'aggregate' must be a non-empty list."

    axis_columns = []
    required_summary_group_by_keys = {"columnName", "tableName"}
    required_summary_aggregate_keys = {"columnName", "operation", "tableName"}

    for gb in group_by:
        if not required_summary_group_by_keys.issubset(gb):
            return "Each 'group_by' entry must have 'columnName' and 'tableName'."
        axis_columns.append({
            "type": "groupBy",
            "columnName": gb["columnName"],
            "operation": "actual",  # grouping doesn't need aggregation
            "tableName": gb["tableName"]
        })

    for ag in aggregate:
        if not required_summary_aggregate_keys.issubset(ag):
            return "Each 'aggregate' entry must have 'columnName', 'operation', and 'tableName'."
        if ag["operation"] == "actual":
            return "Invalid operation 'actual' in aggregate. Use 'sum', 'count', etc."
        axis_columns.append({
            "type": "summarize",
            "columnName": ag["columnName"],
            "operation": ag["operation"],
            "tableName": ag["tableName"]
        })

    config = {
        "baseTableName": table_name,
        "title": report_name,
        "reportType": "summary",
        "axisColumns": axis_columns
    }

    if filters:
        if not isinstance(filters, list):
            return "Filters must be a list of dictionaries."
        for f in filters:
            if not {"columnName", "operation", "filterType", "values", "exclude"}.issubset(f):
                return "Each filter must contain 'columnName', 'operation', 'filterType', 'values', and 'exclude'."
        config["filters"] = filters

    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    report_id = workspace.create_report(config)
    return f"Summary report created successfully. Report ID: {report_id}"


def create_query_table_implementation(org_id, workspace_id, table_name, query):
    analytics_client = get_analytics_client_instance()
    workspace = analytics_client.get_workspace_instance(org_id, workspace_id)
    result = workspace.create_query_table(query, table_name)
    return f"Query table created successfully. Table Id : {result}"


def delete_view_implementation(org_id, workspace_id, view_id):
    analytics_client = get_analytics_client_instance()
    view_instance = analytics_client.get_view_instance(org_id, workspace_id, view_id)
    view_instance.delete()
    return f"View with ID {view_id} deleted successfully."
