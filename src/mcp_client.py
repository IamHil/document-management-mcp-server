import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
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

        print("\nCalling read_doc_contents...")
        edit_result = await client.call_tool(
            "edit_document",
            {
                "doc_id": "report.pdf",
                "old_str": "30m condenser tower",
                "new_str": "25m condenser tower",
            },
        )
        print("\nEdit result:")
        print(edit_result)

        print("\nVerifying document...")

        verify_result = await client.call_tool(
            "read_doc_contents",
            {"doc_id": "report.pdf"},
        )

        print("\nUpdated document:")
        print(verify_result)

        result = await client.call_tool(
            "read_doc_contents",
            {"doc_id": "report.pdf"},
        )

        print("\nTool result:")
        print(result)

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())