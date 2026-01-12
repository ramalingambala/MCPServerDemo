#!/usr/bin/env python3
"""
Simple HTTP server to test the MCP server functionality
This bypasses Azure Functions issues and lets us test the BMI calculator with resources
"""

import mcp_server as shared_mcp
import asyncio
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add shared_code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared_code'))


class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - return server info and available tools"""
        try:
            # Use asyncio to handle async MCP calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            tools_list = loop.run_until_complete(shared_mcp.mcp.list_tools())
            tools = []
            for tool_info in tools_list:
                tools.append({
                    "name": tool_info.get("name", "Unknown"),
                    "description": tool_info.get("description", "No description available")
                })

            response_data = {
                "status": "success",
                "message": "MCP Server is running (Test Mode)",
                "server_name": shared_mcp.mcp.name,
                "available_tools": tools,
                "tool_count": len(tools),
                "resources_available": [
                    "bmi://categories",
                    "bmi://health-risks",
                    "bmi://calculation-guide",
                    "bmi://healthy-weight-tips"
                ]
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(
                response_data, indent=2).encode('utf-8'))

        except Exception as e:
            error_response = {
                "status": "error",
                "message": f"Error getting tools: {str(e)}"
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(
                error_response, indent=2).encode('utf-8'))

    def do_POST(self):
        """Handle POST requests - execute tools"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            tool_name = request_data.get('tool')
            arguments = request_data.get('arguments', {})

            if not tool_name:
                self.send_error_response(
                    400, "Missing 'tool' parameter in request")
                return

            # Use asyncio to handle async MCP calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                shared_mcp.mcp.call_tool(tool_name, arguments))

            response_data = {
                "status": "success",
                "tool": tool_name,
                "result": result,
                "arguments": arguments
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(
                response_data, indent=2).encode('utf-8'))

        except json.JSONDecodeError as e:
            self.send_error_response(400, f"Invalid JSON: {str(e)}")
        except Exception as e:
            self.send_error_response(500, f"Tool execution failed: {str(e)}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_error_response(self, status_code, message):
        """Send an error response"""
        error_response = {
            "status": "error",
            "message": message
        }
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(error_response, indent=2).encode('utf-8'))

    def log_message(self, format, *args):
        """Log messages"""
        print(f"[{self.date_time_string()}] {format % args}")


def run_server():
    """Run the HTTP server"""
    port = 7071
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHandler)

    print(f"MCP Server running on http://localhost:{port}")
    print("Available endpoints:")
    print(f"  GET  http://localhost:{port}/ - Server info and available tools")
    print(f"  POST http://localhost:{port}/ - Execute tools")
    print("\nExample BMI calculation:")
    print(f'  curl -X POST http://localhost:{port}/ \\')
    print('    -H "Content-Type: application/json" \\')
    print(
        '    -d \'{"tool": "calculate_bmi", "arguments": {"weight_kg": 70, "height_m": 1.75}}\'')
    print("\nExample BMI resources:")
    print(f'  curl -X POST http://localhost:{port}/ \\')
    print('    -H "Content-Type: application/json" \\')
    print(
        '    -d \'{"tool": "get_bmi_resources", "arguments": {"resource_type": "categories"}}\'')
    print("\nPress Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
