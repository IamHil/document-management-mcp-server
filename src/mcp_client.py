import asyncio
from contextlib import AsyncExitStack
import json
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Adding Sampling Summarize tool to the client

async def sampling_callback(
        context,
        params: types.CreateMessageRequestParams,

):
    print("Sampling callback invoked with params:")
    return types.CreateMessageResult(
        role="assistant",
        model="local-sampling-demo",
        content=types.TextContent(
            type="text",
            text=(
                "[Sampling Response]\n"
                "The provided text was processed by the MCP client's sampling callback."
            ),
        ),
        stopReson="endTurn",
    )

# Logging and Notification

async def logging_callback(params: types.LoggingMessageNotificationParams):
    print(f"\n[LOG] {params.data}")

async def progress_callback(
    progress: float,
    total: float | None,
    message: str | None
):
    if total is not None:
        percentage = (progress / total) * 100
        print(
            f"[PROGRESS] {progress}/{total} "
            f"({percentage:.1f}%)"
        )
    else:
        print(f"[PROGRESS] {progress}")

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
            ClientSession(self.stdio, self.write, sampling_callback=sampling_callback,logging_callback=logging_callback,)
        )

        await self.session.initialize()

    async def list_tools(self):
        result = await self.session.list_tools()
        return result.tools

    # Adding List prompt functionality to the client
    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session.list_prompts()
        return result.prompts

    # Adding Get Prompt functionality to the client
    async def get_prompt(self, prompt_name:str, args: dict[str, str]):
        result = await self.session.get_prompt(prompt_name, args)
        return result.messages


    async def call_tool(self, tool_name: str, tool_input: dict, progress_callback=None,):
        return await self.session.call_tool(tool_name, tool_input, progress_callback=progress_callback)

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

        print("\nListing available prompts...")
        prompts = await client.list_prompts()
        print("\nAvailable prompts:")
        for prompt in prompts:
            print(f"- {prompt.name}: {prompt.description}")

        print("\nGetting 'format' prompt for 'report.pdf'...")
        messages = await client.get_prompt(
            "format",
            {"doc_id": "report.pdf"}
        )
        print("\nPrompt messages:")
        for message in messages:
            print(message)

        print("\nTesting Sampling...")

        sampling_result = await client.call_tool(
            "summarize",
            {
                "text_to_summarize": (
                    "The Model Context Protocol provides a standardized "
                    "way for AI applications to communicate with external "
                    "tools, resources, and data sources."
                )
            },
        )

        print("\nSampling result:")
        print(sampling_result)

        print("\nTesting logging and progress notifications...")

        process_result = await client.call_tool(
            "process_document",
            {
                "doc_id": "report.pdf"
            },
            progress_callback=progress_callback,
        )

        print("\nProcessing result:")
        print(process_result)

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())