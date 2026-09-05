 # AI Job Search MCP Server

This project provides an MCP server that lets Claude Desktop search the local job dataset.

## Connect to Claude Desktop on Windows

### Check Installations

```powershell
where.exe python
```
```powershell
where.exe uv
```

It gives the path about where it is installed in your machine.

### 1. Confirm the project environment

From the project directory, verify that the virtual environment exists:

```powershell
Test-Path .venv\Scripts\python.exe
```

The command should return `True`.

### 2. Open the Claude Desktop configuration file

Open or create this file:

```text
%APPDATA%\Claude\claude_desktop_config.json or get the path by opening claude desktop
```

If the file already contains other MCP servers, add the `ai-job-search` entry inside the existing `mcpServers` object.

### 3. Add the server configuration

Use the following JSON:

```text
If you are using uv
```

```json
{
	"mcpServers": {
		"ai-job-search": {
			"command": "D:\\VsCode\\my-ai-job-search\\.venv\\Scripts\\python.exe",
			"args": [
				"D:\\VsCode\\my-ai-job-search\\main.py"
			]
		}
	}
}
```

```text
If you are using python
```

```json
{
	"mcpServers": {
		"ai-job-search": {
			"command": "D:\\VsCode\\my-ai-job-search\\.venv\\Scripts\\python.exe",
			"args": [
				"D:\\VsCode\\my-ai-job-search\\main.py"
			]
		}
	}
}
```

The paths use double backslashes because this is a JSON file. Do not replace `main.py` with the package console command; the MCP server is started by `main.py`.

### 4. Restart Claude Desktop

Save the configuration file, exit Claude Desktop completely, and start it again.

### 5. Test the MCP tools

Ask Claude one of these questions:

```text
Search for Java jobs in Chennai with hybrid work mode.
```

```text
Show the statistics for available jobs.
```

```text
Get the details for job ID 1.
```

The available MCP tools are `search_jobs`, `get_job_details`, and `get_job_stats`. The server also provides the `config://app-version` resource and the `job_recommendation_prompt` prompt.

## Troubleshooting

- Make sure Claude Desktop is fully restarted after changing its configuration.
- Confirm that `D:\VsCode\my-ai-job-search\.venv\Scripts\python.exe` exists.
- Confirm that `D:\VsCode\my-ai-job-search\main.py` exists.
- If Claude does not show the server, check Claude Desktop's MCP/server logs for the startup error.
