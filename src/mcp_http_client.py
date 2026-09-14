import asyncio
import json
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client


# Sampling callback
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


# Logging callback
async def logging_callback(
    params: types.LoggingMessageNotificationParams,
):
    print(f"\n[LOG] {params.data}")


# Progress callback
async def progress_callback(
    progress: float,
    total: float | None,
    message: str | None,
):
    if total is not None:
        percentage = (progress / total) * 100
        print(
            f"[PROGRESS] {progress}/{total} "
            f"({percentage:.1f}%)"
        )
    else:
        print(f"[PROGRESS] {progress}")


# Roots callback
async def list_roots_callback(context):
    root_path = Path(__file__).resolve().parent.parent / "sample_documents"

    return types.ListRootsResult(
        roots=[
            types.Root(
                uri=root_path.as_uri(),
                name="Sample Documents",
            )
        ]
    )


class MCPHTTPClient:

    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_server(
        self,
        server_url: str = "http://127.0.0.1:8000/mcp",
    ):
        http_transport = await self.exit_stack.enter_async_context(
            streamable_http_client(server_url)
        )

        self.read_stream, self.write_stream, self.get_session_id = (
            http_transport
        )

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                self.read_stream,
                self.write_stream,
                sampling_callback=sampling_callback,
                logging_callback=logging_callback,
                list_roots_callback=list_roots_callback,
            )
        )

        await self.session.initialize()

        print("\nConnected to MCP server over Streamable HTTP!")

        session_id = self.get_session_id()

        if session_id:
            print(f"Session ID: {session_id}")

    async def list_tools(self):
        result = await self.session.list_tools()
        return result.tools

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session.list_prompts()
        return result.prompts

    async def get_prompt(
        self,
        prompt_name: str,
        args: dict[str, str],
    ):
        result = await self.session.get_prompt(prompt_name, args)
        return result.messages

    async def call_tool(
        self,
        tool_name: str,
        tool_input: dict,
        progress_callback=None,
    ):
        return await self.session.call_tool(
            tool_name,
            tool_input,
            progress_callback=progress_callback,
        )

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

    client = MCPHTTPClient()

    try:

        await client.connect_to_server()

        print("\nAvailable tools:")

        tools = await client.list_tools()

        for tool in tools:
            print(f"\n- {tool.name}")
            print(f"  Description: {tool.description}")

        print("\nReading document list resource...")

        documents = await client.read_resource(
            "docs://documents"
        )

        print("\nDocument list:")
        print(documents)

        print("\nReading report.pdf resource...")

        report = await client.read_resource(
            "docs://documents/report.pdf"
        )

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
            {"doc_id": "report.pdf"},
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

        print("\nTesting MCP Roots...")

        roots_result = await client.call_tool(
            "list_root_documents",
            {}
        )

        print("\nFiles available through Roots:")
        print(roots_result)

        print("\nTesting allowed root file...")

        allowed_file = (
            Path(__file__).resolve().parent.parent
            / "sample_documents"
            / "report.txt"
        )

        allowed_result = await client.call_tool(
            "read_root_file",
            {
                "file_path": str(allowed_file)
            }
        )

        print("\nAllowed file result:")
        print(allowed_result)

    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())