# Zoho Analytics MCP Server

## 1. Overview

This documentation covers the Model Context Protocol (MCP) server for Zoho Analytics, providing information on installation, setup, and available tools.

## 2. Table of Contents

- [1. Overview](#1-overview)
- [2. Table of Contents](#2-table-of-contents)
- [3. Getting Started](#3-getting-started)
  - [3.1. Docker Image Setup](#31-docker-image-setup)
    - [3.1.1. Build from Source](#311-build-from-source)
    - [3.1.2. Pull from Docker Registry](#312-pull-from-docker-registry)
  - [3.2. Environment Variables](#32-environment-variables)
    - [3.2.1. OAuth Token](#321-oauth-token)
  - [3.3. Configuration with MCP Hosts](#33-configuration-with-mcp-hosts)
    - [3.3.1. Claude Desktop](#331-claude-desktop)
    - [3.3.2. VSCode](#332-vscode)
- [4. Tools List](#4-tools-list)
- [5. Troubleshooting](#5-troubleshooting)
- [6. Support](#6-support)

## 3. Getting Started

### 3.1. Docker Image Setup

For Docker based setups, please make sure to have `docker` and a `container runtime` installed.

#### 3.1.1. Build from Source

To build the Zoho Analytics MCP server from source, you need to have Docker installed on your system.

```bash
# Clone the repository
git clone https://github.com/your-org/zoho_analytics_mcp.git
cd zoho_analytics_mcp/docker

# Build the Docker image
docker build -t mcp/zoho_analytics .
```

#### 3.1.2. Pull from Docker Registry

Currently, there is no public Docker registry hosting the Zoho Analytics MCP image. Please build from source using the instructions above.

### 3.2. Environment Variables

The MCP server requires the following environment variables:

| Variable | Description |
|----------|-------------|
| `ANALYTICS_CLIENT_ID` | Your Zoho Analytics OAuth client ID |
| `ANALYTICS_CLIENT_SECRET` | Your Zoho Analytics OAuth client secret |
| `ANALYTICS_REFRESH_TOKEN` | Your Zoho Analytics OAuth refresh token |
| `ANALYTICS_ORG_ID` | Your Zoho Analytics organization ID |
| `ANALYTICS_MCP_DATA_DIR` | Directory for storing temporary data files |
| `ANALYTICS_DC_LOCATION` | Your Zoho Analytics data center location (US, EU, IN, AU, JP, CN) |

#### 3.2.1. OAuth Token

To obtain the OAuth credentials required for the environment variables, follow these steps:

1. Go to the [Zoho Developer Console](https://api-console.zoho.com/)
2. Create a new Self-Client application
3. Enable the Zoho Analytics API scope
4. Generate a refresh token

You will need these credentials to configure the MCP server for use with Zoho Analytics.

### 3.3. Configuration with MCP Hosts

#### 3.3.1. Claude Desktop

To configure the Zoho Analytics MCP server with Claude Desktop, add the following configuration to your Claude settings:

```json
{
  "mcpServers": {
    "ZohoAnalyticsMCP": {
      "command": "docker",
      "args": [
        "run",
        "-e", "ANALYTICS_CLIENT_ID=<YOUR_ANALYTICS_CLIENT_ID>",
        "-e", "ANALYTICS_CLIENT_SECRET=<YOUR_ANALYTICS_CLIENT_SECRET>",
        "-e", "ANALYTICS_REFRESH_TOKEN=<YOUR_ANALYTICS_REFRESH_TOKEN>",
        "-e", "ANALYTICS_ORG_ID=<YOUR_ANALYTICS_ORG_ID>",
        "-e", "ANALYTICS_MCP_DATA_DIR=<YOUR_ANALYTICS_MCP_DATA_DIR>",
        "-e", "ANALYTICS_DC_LOCATION=<YOUR_ANALYTICS_DC>",
        "--network=host",
        "-i",
        "--rm",
        "-v", "<YOUR_ANALYTICS_MCP_DATA_DIR>:<YOUR_ANALYTICS_MCP_DATA_DIR>",
        "mcp/zoho_analytics"
      ]
    }
  }
}
```

Replace the placeholders with your actual Zoho Analytics credentials. 


#### 3.3.2. VSCode

To configure the Zoho Analytics MCP server with Visual Studio Code:

1. Install the MCP extension for VSCode
2. Add the following configuration to your `settings.json` file:

```json
"mcp": {
  "servers": {
    "zoho_analytics_mcp_server": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "-e", "ANALYTICS_CLIENT_ID=<YOUR_ANALYTICS_CLIENT_ID>",
        "-e", "ANALYTICS_CLIENT_SECRET=<YOUR_ANALYTICS_CLIENT_SECRET>",
        "-e", "ANALYTICS_REFRESH_TOKEN=<YOUR_ANALYTICS_REFRESH_TOKEN>",
        "-e", "ANALYTICS_ORG_ID=<YOUR_ANALYTICS_ORG_ID>",
        "-e", "ANALYTICS_MCP_DATA_DIR=<YOUR_LOCAL_DATA_DIR>",
        "-e", "ANALYTICS_DC_LOCATION=<YOUR_ANALYTICS_DC>",
        "--network=host",
        "-i",
        "--rm",
        "-v", "<YOUR_LOCAL_DATA_DIR>:<YOUR_LOCAL_DATA_DIR>",
        "mcp/zoho_analytics"
      ]
    }
  }
}
```


## 4. Tools List

The MCP server provides various tools for interacting with Zoho Analytics.

<table>
    <thead>
        <tr>
            <th>Tool</th>
            <th>Description</th>
        </tr>
    </thead>
    <tbody>
        <!-- Data Tools -->
        <tr>
            <td><code>analyse_file_structure</code></td>
            <td>Analyzes the structure of a CSV or JSON file to determine its columns and data types.</td>
        </tr>
        <tr>
            <td><code>download_file</code></td>
            <td>Downloads a file from a given URL and saves it to a local directory.</td>
        </tr>
        <tr>
            <td><code>import_data</code></td>
            <td>Imports data into a specified table from a file or a list of dictionaries.</td>
        </tr>
        <tr>
            <td><code>export_view</code></td>
            <td>Exports an object (table, chart, or dashboard) from the workspace in the specified format.</td>
        </tr>
        <tr>
            <td><code>query_data</code></td>
            <td>Executes a SQL query on the specified workspace and returns the results.</td>
        </tr>
        <tr>
            <td><code>get_workspaces_list</code></td>
            <td>Fetches the list of workspaces in the user's organization.</td>
        </tr>
        <tr>
            <td><code>get_view_list</code></td>
            <td>Fetches the list of views (tables, reports, dashboards) within a specified workspace.</td>
        </tr>
        <tr>
            <td><code>get_view_details</code></td>
            <td>Fetches the details of a specific view including its structure and properties.</td>
        </tr>
        <tr>
            <td><code>create_workspace</code></td>
            <td>Creates a new workspace in Zoho Analytics with the given name.</td>
        </tr>
        <tr>
            <td><code>create_table</code></td>
            <td>Creates a new table in a specified workspace with defined columns.</td>
        </tr>
        <tr>
            <td><code>create_aggregate_formula</code></td>
            <td>Creates an aggregate formula in a specified table that returns a single aggregate value.</td>
        </tr>
        <tr>
            <td><code>create_chart_report</code></td>
            <td>Creates a chart report (bar, line, pie, scatter, bubble) in the specified workspace.</td>
        </tr>
        <tr>
            <td><code>create_pivot_report</code></td>
            <td>Creates a pivot table report for multidimensional data analysis.</td>
        </tr>
        <tr>
            <td><code>create_summary_report</code></td>
            <td>Creates a summary report that groups data by specified columns and applies aggregate functions.</td>
        </tr>
        <tr>
            <td><code>create_lookup</code></td>
            <td>Creates a lookup relationship between two tables based on a common column.</td>
        </tr>
        <tr>
            <td><code>create_custom_formula_column</code></td>
            <td>Creates a custom formula column derived from existing columns using a SQL expression.</td>
        </tr>
        <tr>
            <td><code>create_query_table</code></td>
            <td>Creates a query table based on a SQL query for derived data views.</td>
        </tr>
        <tr>
            <td><code>delete_view</code></td>
            <td>Deletes a view (table, report, or dashboard) from a workspace.</td>
        </tr>
        <tr>
            <td><code>add_row</code></td>
            <td>Adds a new row to a specified table.</td>
        </tr>
        <tr>
            <td><code>delete_rows</code></td>
            <td>Deletes rows from a specified table based on given criteria.</td>
        </tr>
        <tr>
            <td><code>update_rows</code></td>
            <td>Updates rows in a specified table based on given criteria.</td>
        </tr>
    </tbody>
</table>

## 5. Troubleshooting

If you encounter issues with the MCP server:

1. Verify that your environment variables are correctly set
2. Check that your OAuth tokens are valid and have appropriate permissions
3. Ensure your Docker installation is working correctly
4. Confirm that your data center location is set correctly (US, EU, IN, AU, JP, CN)
5. Make sure the specified data directory exists and has proper permissions

## 6. Support

For additional support, please contact the Zoho Analytics support team
