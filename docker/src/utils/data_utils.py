from config import get_analytics_client_instance
import time
import csv
import os

QUERY_DATA_ROW_LIMIT = os.getenv("QUERY_DATA_RESULT_ROW_LIMITS") or 20
QUERY_DATA_POLLING_INTERVAL = os.getenv("QUERY_DATA_POLLING_INTERVAL") or 4
QUERY_DATA_QUEUE_TIMEOUT = os.getenv("QUERY_DATA_QUEUE_TIMEOUT") or 120
QUERY_DATA_QUERY_EXECUTION_TIMEOUT = os.getenv("QUERY_DATA_QUERY_EXECUTION_TIMEOUT") or 30


def poll_job_completion(bulk, job_id, status_messages, polling_interval=None, queue_timeout=None, execution_timeout=None):
    if polling_interval is None:
        polling_interval = QUERY_DATA_POLLING_INTERVAL
    if queue_timeout is None:
        queue_timeout = QUERY_DATA_QUEUE_TIMEOUT
    if execution_timeout is None:
        execution_timeout = QUERY_DATA_QUERY_EXECUTION_TIMEOUT
    start_time = time.time()
    processing_start_time = None
    while True:
        job_details = bulk.get_export_job_details(job_id)
        current_time = time.time()
        if job_details['jobCode'] == '1004': # code for JOB COMPLETED
            break
        elif job_details['jobCode'] == '1003': # code for ERROR OCCURRED
            return status_messages.get('error', "Some internal error occurred. Please try again later.")
        elif job_details['jobCode'] == '1001': # code for JOB NOT INITIATED
            if current_time - start_time > queue_timeout:
                return status_messages.get('queue_timeout', "Job accepted, but queue processing is slow. Please try again later.")
        elif job_details['jobCode'] == '1002': # code for JOB IN PROGRESS
            if processing_start_time is None:
                processing_start_time = current_time
            elif current_time - processing_start_time > execution_timeout:
                return status_messages.get('execution_timeout', "Job is taking too long to execute. Please try again later.")
        time.sleep(polling_interval)
    return None


def query_data_implementation(org_id, workspace_id, sql_query):
    try:
        file_path = "/tmp/query_data_result.csv"
        analytics_client = get_analytics_client_instance()
        bulk = analytics_client.get_bulk_instance(org_id, workspace_id)
        job_id = bulk.initiate_bulk_export_using_sql(sql_query, "CSV")
        status_messages = {
            'error': "Some internal error ocurred (Not likely due to the query). Please try again later.",
            'queue_timeout': "Query Job accepted, but queue processing is slow. Please try again later.",
            'execution_timeout': "Query is taking too long to execute, maybe due to the complexity. Please try a simpler query"
        }
        error_message = poll_job_completion(bulk, job_id, status_messages)
        if error_message:
            return error_message
        file_path = "/tmp/" + job_id + ".csv"
        bulk = analytics_client.get_bulk_instance(org_id, workspace_id)
        bulk.export_bulk_data(job_id, file_path)
        result = []
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i >= QUERY_DATA_ROW_LIMIT:
                    break
                result.append(row)        
        return result[:QUERY_DATA_ROW_LIMIT]
    except Exception as e:
        raise e
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    

def import_data_implementation(org_id, workspace_id, file_path, table_id, file_type, data):
    analytics_client = get_analytics_client_instance()
    bulk = analytics_client.get_bulk_instance(org_id, workspace_id)
    if file_path:
        if file_path.startswith("https"):
            return "File path cannot be a remote URL. Please download the file using the download_file tool and provide the local file path."
        if not os.path.exists(file_path):
            return f"File {file_path} does not exist. Please provide a valid local file path."
        if file_type not in ["csv", "json"]:
            return "Invalid file type. Please provide 'csv' or 'json'."
        result = bulk.import_data(table_id, "append", file_type, "true", file_path, config={"delimiter":'0'})
        return result
    if not data:
        return "No data provided to import. Please provide either 'data' or 'local_file_path'."
    result = bulk.import_raw_data(table_id, "append", "json", "true", data, config={"delimiter":'0'})
    return result


def export_view_implementation(org_id, response_file_format, response_file_path, workspace_id, view_id):
    if response_file_format not in ["csv", "json", "xml", "xls", "pdf", "html", "image"]:
        return "Invalid response file format. Supported formats are ['csv', 'json', 'xml', 'xls', 'pdf', 'html', 'image']."

    analytics_client = get_analytics_client_instance()
    bulk = analytics_client.get_bulk_instance(org_id, workspace_id)
    try:
        bulk.export_data(view_id, response_file_format, response_file_path)
    except Exception as e:
        if hasattr(e, 'errorCode') and e.errorCode == 8133:
            if response_file_format != "pdf":
                return f"Exporting view {view_id} in {response_file_format} format is not supported. Please use 'pdf' format for dashboards."
            job_id = bulk.initiate_bulk_export(view_id, response_format="pdf", config={"dashboardLayout":1})
            status_messages = {
                'error': "Some internal error ocurred. Please try again later.",
                'queue_timeout': "Dashboard export Job accepted, but queue processing is slow. Please try again later.",
                'execution_timeout': "Dashboard is taking too long to export, maybe due to the complexity. Please try a again later."
            }
            error_message = poll_job_completion(bulk, job_id, status_messages)
            if error_message:
                return error_message
            bulk.export_bulk_data(job_id, response_file_path)
        else:
            raise e
    return f"Object exported successfully to {response_file_path} in {response_file_format} format."

