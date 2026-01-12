#!/usr/bin/env python3
"""
Simple HTTP server for testing MCP BMI Calculator
This provides the same API as Azure Functions for testing with Postman/curl
"""

import asyncio
import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Add shared_code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'shared_code'))

try:
    import mcp_server as shared_mcp
    mcp = shared_mcp.mcp
    logger = shared_mcp.logger
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MCP server import failed: {e}")
    MCP_AVAILABLE = False
    logger = logging.getLogger(__name__)


class MCPHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests - return server info and available tools"""
        try:
            if not MCP_AVAILABLE:
                self.send_error_response(500, "MCP server not available")
                return

            # Use asyncio to handle async MCP calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            tools_list = loop.run_until_complete(mcp.list_tools())
            tools = []
            for tool_info in tools_list:
                tools.append({
                    "name": tool_info.name,
                    "description": tool_info.description
                })

            response_data = {
                "status": "success",
                "message": "MCP Server is running (Local Test Mode)",
                "server_name": mcp.name,
                "available_tools": tools,
                "tool_count": len(tools),
                "endpoints": {
                    "get_tools": "GET /",
                    "execute_tool": "POST /",
                    "bmi_example": "POST / with {'tool': 'calculate_bmi', 'arguments': {'weight_kg': 70, 'height_m': 1.75}}"
                }
            }

            self.send_json_response(200, response_data)

        except Exception as e:
            logger.error(f"Error in GET handler: {e}")
            self.send_error_response(500, f"Error getting tools: {str(e)}")

    def do_POST(self):
        """Handle POST requests - execute tools"""
        try:
            if not MCP_AVAILABLE:
                self.send_error_response(500, "MCP server not available")
                return

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
                mcp.call_tool(tool_name, arguments))

            # Process result based on MCP response format
            if isinstance(result, tuple) and len(result) >= 2:
                # Extract the actual result from MCP response
                actual_result = result[1].get('result', result[0])
                if isinstance(actual_result, list) and actual_result:
                    # Handle TextContent objects
                    text_content = actual_result[0]
                    if hasattr(text_content, 'text'):
                        tool_result = text_content.text
                    else:
                        tool_result = str(actual_result)
                else:
                    tool_result = actual_result
            else:
                tool_result = str(result)

            response_data = {
                "status": "success",
                "tool": tool_name,
                "arguments": arguments,
                "result": tool_result,
                "result_type": type(tool_result).__name__
            }

            self.send_json_response(200, response_data)

        except json.JSONDecodeError as e:
            self.send_error_response(400, f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            self.send_error_response(500, f"Tool execution failed: {str(e)}")

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json_response(self, status_code, data):
        """Send a JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """Send an error response"""
        error_response = {
            "status": "error",
            "message": message,
            "error_code": status_code
        }
        self.send_json_response(status_code, error_response)

    def log_message(self, format, *args):
        """Custom log message format"""
        print(f"[{self.date_time_string()}] {format % args}")


def run_server():
    """Run the HTTP server"""
    port = 7071
    server_address = ('', port)
    httpd = HTTPServer(server_address, MCPHTTPHandler)

    print("🚀 MCP BMI Calculator Server")
    print("=" * 50)
    print(f"Server running on http://localhost:{port}")
    print(
        f"Status: {'✅ MCP Available' if MCP_AVAILABLE else '❌ MCP Import Failed'}")
    print()
    print("📋 Available Endpoints:")
    print(f"  GET  http://localhost:{port}/")
    print("    - Returns server info and available tools")
    print()
    print(f"  POST http://localhost:{port}/")
    print("    - Execute MCP tools")
    print("    - Content-Type: application/json")
    print()
    print("🧪 Test Examples:")
    print()
    print("1. Get server info:")
    print(f"   curl http://localhost:{port}/")
    print()
    print("2. Calculate BMI:")
    print(f'   curl -X POST http://localhost:{port}/ \\')
    print('     -H "Content-Type: application/json" \\')
    print(
        '     -d \'{"tool": "calculate_bmi", "arguments": {"weight_kg": 70, "height_m": 1.75}}\'')
    print()
    print("3. Get BMI resources:")
    print(f'   curl -X POST http://localhost:{port}/ \\')
    print('     -H "Content-Type: application/json" \\')
    print(
        '     -d \'{"tool": "get_bmi_resources", "arguments": {"resource_type": "categories"}}\'')
    print()
    print("4. Test SQL connectivity:")
    print(f'   curl -X POST http://localhost:{port}/ \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"tool": "test_network_connectivity", "arguments": {}}\'')
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        httpd.server_close()
        print("✅ Server stopped")


if __name__ == '__main__':
    run_server()
