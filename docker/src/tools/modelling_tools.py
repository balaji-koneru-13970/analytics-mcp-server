from mcp_instance import mcp
from config import Config, get_analytics_client_instance
from utils.common import retry_with_fallback
from utils.modelling_utils import (
    create_workspace_implementation, 
    create_table_implementation,
    create_aggregate_formula_implementation,
    create_chart_report_implementation,
    create_pivot_report_implementation,
    create_summary_report_implementation,
    create_query_table_implementation,
    delete_view_implementation
)

ALLOWED_CHART_TYPES = ["bar", "line", "pie", "scatter", "bubble"]
REQUIRED_FILTER_KEYS = {"columnName", "operation", "filterType", "values", "exclude"}
REQUIRED_PIVOT_AXIS_KEYS = {"columnName", "tableName", "operation"}
REQUIRED_SUMMARY_GROUP_BY_KEYS = {"columnName", "tableName"}
REQUIRED_SUMMARY_AGGREGATE_KEYS = {"columnName", "operation", "tableName"}


@mcp.tool()
def create_workspace(workspace_name: str, org_id: str | None = None) -> str:
    """
    <use_case>
        Create a new workspace in zoho analytics with the given name.
    </use_case>

    <important_notes>
        A workspace is a container for related zoho analytics objects like tables, reports, and dashboards.
    </important_notes>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], None, None, create_workspace_implementation, workspace_name=workspace_name)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the workspace : {error_message}"


@mcp.tool()
def create_table(workspace_id: str, table_name: str, columns_list: list[dict], org_id: str | None = None) -> str:
    """
    <use_case>
        Create a new table in the given workspace with the given name.
    </use_case>

    <arguments>
        workspace_id (str): The ID of the workspace in which to create the table.
        table_name (str): The name of the table to create.
        columns_list (list[dict]): A list of dictionaries representing the columns of the table.
            Each dictionary should contain the following keys:
                - "COLUMNNAME": The name of the column.
                - "DATATYPE": The data type of the column ("PLAIN", "NUMBER", "DATE").
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_table_implementation, 
                                   workspace_id=workspace_id, table_name=table_name, columns_list=columns_list)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the table : {error_message}"


@mcp.tool()
def create_aggregate_formula(workspace_id: str, table_id: str, expression: str, formula_name: str, org_id: str | None = None) -> str:
    """
    <use_case>
        Create an aggregate formula in the specified table of the workspace.
    </use_case>

    <important_notes>
        1. Aggregate Formulas in zoho analytics are select query expression that returns a single aggregate value as output.
        2. The expression should always return a valid aggregate value.
        3. Any Column or Table names used should be enclosed in double quotes. Literal values should be enclosed in single quotes.
        4. While the expression can contain complex nested functions, it should always return a single aggregate value.
        5. Assume that the expression is mysql compatible.
    </important_notes>

    <arguments>
        1. workspace_id (str): The ID of the workspace.
        2. table_id (str): The ID of the table.
        3. expression (str): The expression for the aggregate formula.
            For example, SUM("Revenue") or AVG("Salary").
            The expression should be a valid SQL aggregate function.
        4. formula_name (str): The name of the aggregate formula.
        5. org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>

    <returns>
        str: The result of the operation. If successful, it returns the ID of the created aggregate formula.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_aggregate_formula_implementation, workspace_id=workspace_id,
                                  table_id=table_id, expression=expression, formula_name=formula_name)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the aggregate formula : {error_message}"


@mcp.tool()
def create_chart_report(workspace_id: str, table_name: str, chart_name: str, chart_details: dict, filters: list[dict] | None = None, org_id: str | None = None) -> str:
    """
    <use_case>
    - Create a chart report in the specified workspace for a table in Zoho Analytics.
    - Use this to generate visual representations of data using bar, line, pie, scatter, or bubble charts.
    </use_case>

    <important_notes>
    - A chart is a report that visually represents data from a table or multiple tables.
    - If y-axis operation is "actual", only "scatter" chart is allowed. For all other chart types, use "sum" for numeric columns and "count" for string columns in y-axis.
    - charts can include filters to narrow down the dataset.
    - chart can be created over columns from the same table or from other tables with which a relationship is defined.
    - For x-axis operations for numeric columns, use "measure" or "dimension" instead of "actual", depending upon the type of the numeric column.
    </important_notes>

    <arguments>
    - workspace_id (str): ID of the workspace to create the chart in.
    - table_name (str): The base table name for the chart.
    - chart_name (str): Desired name for the chart report.
    - chart_details (dict): Details of the chart including:
        - chartType (str): One of ["bar", "line", "pie", "scatter", "bubble"]
        - x_axis (dict):
            - columnName (str)
            - operation (str): (strings) actual, count, distinctCount | (numbers) sum, average, min, max, measure, dimension, count, distinctCount  | (dates) year, month, week, fullDate, dateTime, range, count, distinctCount. 
            - tableName (optional [str]): If the column belongs to another table with which a relationship is defined with base table, provide the tableName.
        - y_axis (dict): Same structure as x_axis
    - filters (list[dict] | None): Optional. Filter definitions per <filters_args>.
    - org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.

        <filters_args>
            - tableName (str): The name of the table containing the column to filter.
            - columnName (str): The name of the column to filter.
            - operation (str): Specifies the function applied to the specified column used in the filter. The accepted functions differ based on the data type of the column.
                Date: actual, seasonal, relative
                String: actual, count, distinctCount
                Number: measure, dimension, sum, average, min, max, count, distinctCount
            - filterType (str): The type of filter to apply. Accepted values: individualValues, range, ranking, rankingPct, dateRange, year, quarterYear, monthYear, weekYear, quarter, month, week, weekDay, day, hour, dateTime
            - values (list): The values to filter on.
                Example:
                - For individualValues: "value1", "value2"
                - For range: "10 to 20", "50 and above"
                - For ranking: "top 10", "bottom 5"
            - exclude (bool): Whether to exclude or include the filtered values. Default is False.
        </filters_args>
    </arguments>

    <returns>
    - str: Chart creation status or error message.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_chart_report_implementation,workspace_id=workspace_id,
                                   table_name=table_name, chart_name=chart_name, 
                                   chart_details=chart_details, filters=filters)
    except Exception as e:
        if hasattr(e, 'message') and 'Invalid input' in e.message and 'operation' in e.message and 'actual' in e.message:
            return "Invalid operation 'actual' for numeric column. Use 'sum' or 'count' instead."
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the chart report: {error_message}"


@mcp.tool()
def create_pivot_report(workspace_id: str, table_name: str, report_name: str, pivot_details: dict, filters: list[dict] | None = None, org_id: str | None = None) -> str:
    """
    <use_case>
    - Create a pivot table report in the specified workspace and table in Zoho Analytics.
    - Use this when user needs multidimensional data summaries by defining rows, columns, and data fields.
    </use_case>

    <important_notes>
    - All pivot details (row, column, data) are optional individually but atleas one of them must be provided and valid.
    - Allowed operations:
        - String columns: actual, count, distinctCount
        - Number columns: measure, dimension, sum, average, min, max, count
        - Date columns: year, month, week, day
    - Data fields require aggregate operations like sum, count, etc.
    - Lookup fields from other tables can be used if lookup is already defined.
    - For row and column fields, prefer non-aggregate operations like actual, measure or dimension depending on the data type. For data fields, prefer aggregate operations like sum, count, etc.
    </important_notes>

    <arguments>
    - workspace_id (str): ID of the workspace to create the report in.
    - table_name (str): Base table name for the report.
    - report_name (str): Desired name of the pivot report.
    - pivot_details (dict): Contains:
        - row (optional(list[dict])): Each dict must have 'columnName' and 'tableName' and 'operation'.
        - column (optional(list[dict])): Same structure as row.
        - data (optional(list[dict])): same structure as row.
    - filters (list[dict] | None): Optional filters to restrict data scope. Filter definitions per <filters_args>.
    - org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.

    <filters_args>
        - tableName (str): The name of the table containing the column to filter.
        - columnName (str): The name of the column to filter.
        - operation (str): Specifies the function applied to the specified column used in the filter. The accepted functions differ based on the data type of the column.
            Date: actual, seasonal, relative
            String: actual, count, distinctCount
            Number: sum, average, min, max
        - filterType (str): The type of filter to apply. Accepted values: individualValues, range, ranking, rankingPct, dateRange, year, quarterYear, monthYear, weekYear, quarter, month, week, weekDay, day, hour, dateTime
        - values (list): The values to filter on.
            Example:
            - For individualValues: "value1", "value2"
            - For range: "10 to 20"
            - For ranking: "top 10", "bottom 5"
        - exclude (bool): Whether to exclude or include the filtered values. Default is False.
    </filters_args>
    </arguments>

    <returns>
    - str: Report creation result or error message.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_pivot_report_implementation,workspace_id=workspace_id,
                                  table_name=table_name, report_name=report_name, 
                                  pivot_details=pivot_details, filters=filters)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the pivot report: {error_message}"


@mcp.tool()
def create_summary_report(workspace_id: str, table_name: str, report_name: str, summary_details: dict, filters: list[dict] | None = None, org_id: str | None = None) -> str:
    """
    <use_case>
    - Create a summary report in the specified workspace and table in Zoho Analytics.
    - Use this to generate grouped aggregate reports, ideal for quick summaries with group-by and aggregate logic.
    - Creates a summary table that groups data by specified columns and applies aggregate functions.
    </use_case>

    <important_notes>
    - Do NOT use "actual" operation for numeric columns in aggregate. Use "sum" instead.
    - You can use lookup columns from other tables if relationships are already defined.
    </important_notes>

    <arguments>
    - workspace_id (str): The ID of the workspace to create the Summary report in.
    - table_name (str): The name of the base table for the summary report.
    - report_name (str): The name for the Summary to be created.
    - summary_details (dict): Contains:
        - group_by (list[dict]): Each dict must have:
            - columnName (str)
            - tableName (str)
        - aggregate (list[dict]): Each dict must have:
            - columnName (str)
            - operation (str): sum, average, count, min, max, etc.
            - tableName (str): Need to be provided if the column belongs to another table with which a lookup is defined.
    - filters (list[dict] | None): Optional filters. See <filters_args> in create_chart tool.
    - org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.

    <filters_args>
        - tableName (str): The name of the table containing the column to filter.
        - columnName (str): The name of the column to filter.
        - operation (str): Specifies the function applied to the specified column used in the filter. The accepted functions differ based on the data type of the column.
            Date: actual, seasonal, relative
            String: actual, count, distinctCount
            Number: sum, average, min, max
        - filterType (str): The type of filter to apply. Accepted values: individualValues, range, ranking, rankingPct, dateRange, year, quarterYear, monthYear, weekYear, quarter, month, week, weekDay, day, hour, dateTime
        - values (list): The values to filter on.
            Example:
            - For individualValues: "value1", "value2"
            - For range: "10 to 20"
            - For ranking: "top 10", "bottom 5"
        - exclude (bool): Whether to exclude or include the filtered values. Default is False.
    </filters_args>

    </arguments>

    <returns>
    - str: Summary creation status or detailed error message.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_summary_report_implementation,workspace_id=workspace_id,
                                  table_name=table_name, report_name=report_name, 
                                  summary_details=summary_details, filters=filters)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the summary report: {error_message}"


@mcp.tool()
def create_query_table(workspace_id: str, table_name: str, query: str, org_id: str | None = None) -> str:
    """
    <use_case>
        1. Create a query table in the specified workspace with the given name and SQL query.
        2. Used when user needs to create a derived table based on a SQL query.
        3. Used when further transformations are needed on existing tables.
    </use_case>

    <important_notes>
        1. Query Tables in Zoho Analytics are derived tables created from a SQL query.
        2. The query should be a valid SQL query that returns a result set.
        3. Query tables can be used in charts and other reports just like regular tables.
        4. The query should be a valid MYSQL compatible select query.
    </important_notes>

    <arguments>
        workspace_id (str): The ID of the workspace in which to create the query table.
        table_name (str): The name of the query table to create.
        query (str): The SQL select query to create the query table.
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>

    <returns>
        str: The result of the operation. If successful, it returns the ID of the created query table.
    </returns>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", create_query_table_implementation, workspace_id=workspace_id,
                                  table_name=table_name, query=query)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while creating the query table : {error_message}"


@mcp.tool()
def delete_view(workspace_id: str, view_id: str, org_id: str | None = None) -> str:
    """
    <use_case>
        Delete a view (table, report, or dashboard) in the specified workspace.
    </use_case>
    
    <arguments>
        workspace_id (str): The ID of the workspace containing the view.
        view_id (str): The ID of the view to delete.
        org_id (str | None): The ID of the organization to which the workspace belongs to. If not provided, it defaults to the organization ID from the configuration.
    </arguments>
    """
    try:
        if not org_id:
            org_id = Config.ORG_ID
        return retry_with_fallback([org_id], workspace_id, "WORKSPACE", delete_view_implementation, workspace_id=workspace_id,view_id=view_id)
    except Exception as e:
        error_message = e.message if hasattr(e, 'message') else str(e)
        return f"An error occurred while deleting the view: {error_message}"