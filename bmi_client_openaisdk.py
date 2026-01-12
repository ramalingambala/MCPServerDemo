import asyncio
from openai import OpenAI
from mcp.client.stdio import stdio_client
import os
import json
from mcp import ClientSession
from mcp.server import MCPServerStdio
from mcp import Agent, Runner, Trace

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError(
        "Missing OPENAI_API_KEY environment variable for OpenAI client")
client = OpenAI(api_key=str(api_key))
model = "gpt-3.5-turbo"
instruction = """
You are a helpful BMI assistant calculate BMI for a person with a provided weight e.g 70kg and height e.g 1.75m
"""


async def process_bmi_request(query):
    params = {"command": "uv", "args": ["run", "bmi_server.py"]}
    async with MCPServerStdio(params=params) as server:
        mcp_tools = await server.list_tools()
        agent = Agent(
            name="BMI Calculator",
            instructions=instruction,
            model=model,
            mcp_servers=[server]
        )
        with trace("investigate"):
            result = await Runner.run(agent, query)
            return result.final_output


async def main():
    query = "Calculate BMI for height 5ft 10inches and weight 80kg"
    print(f"Sending query: {query}")
    result = await process_bmi_request(query)
    print(f"Result: {result}")
