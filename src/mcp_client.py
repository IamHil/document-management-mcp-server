import asyncio
from contextlib import AsyncExitStack
import json
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


class MCPClient:

    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(self, server_script_path: str):
        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path],
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

    async def list_tools(self):
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, tool_input: dict):
        return await self.session.call_tool(tool_name, tool_input)

    async def read_resource(self, uri: str):

        result = await self.session.read_resource(uri)
    
        resource = result.contents[0]

        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)

            return resource.text

        return resource
    


    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = MCPClient()

    try:
        await client.connect_to_server("src/server.py")

        tools = await client.list_tools()

        print("\nConnected to MCP server!")
        print("\nAvailable tools:")

        for tool in tools:
            print(f"\n- {tool.name}")
            print(f"  Description: {tool.description}")

        print("\nReading document list resource....")

        documents = await client.read_resource("docs://documents")
        print("\nDocument list:")
        print(documents)

        print("\nReading report.pdf resource...")

        report = await client.read_resource("docs://documents/report.pdf")
        print("\nReport contents:")
        print(report)

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())