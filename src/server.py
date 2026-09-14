from mcp.server.fastmcp import FastMCP , Context
from pydantic import Field
from mcp import types
import asyncio
from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname


mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc_contents",
    description="Reads the contents of a document given its name.",
)

def read_document(
    doc_id: str = Field(description="Id of the document to read")
):
    if doc_id not in docs:
        raise ValueError(f"Document with id '{doc_id}' not found.")
    
    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the document content with a new string."
)

def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace."
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text."
    ),
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    if old_str not in docs[doc_id]:
        raise ValueError(f"Text not found in document: {old_str}")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)

    return f"Document '{doc_id}' updated successfully."

@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)

def list_docs() -> list[str]:
    return list(docs.keys())

@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)

def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    return docs[doc_id]

#  Adding Sampling Summarize tool 

@mcp.tool(
    name="summarize",
    description="Summarizes the contents of a document."
)

async def summarize(
    text_to_summarize: str = Field(
        description="The text to summarize."
    ),
    ctx: Context = None,
    
) -> str:

    prompt = f"""   
    Please summarize the following text:

    {text_to_summarize}

    """

    result = await ctx.session.create_message(
        messages=[
            types.SamplingMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=prompt
                )
            )
        ],
        max_tokens=4000,
        system_prompt="You are a helpful assistant that summarizes text.",

    )

    if result.content.type == "text":
        return result.content.text

    raise ValueError("Unexpected content type in summarize result: {result.content.type}")


@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format."
)

def format_document(
    doc_id: str = Field(description="Id of the document to format")

) -> list[types.PromptMessage]:

    prompt = f"""
Your goal is to reformat a document to be written with Markdown syntax.

The id of the document you need to reformat is:
<document_id>{doc_id}</document_id>

Use the read_doc_contents tool to read the contents of the document. 
Then, rewrite the contents in Markdown format. 
Add headers, bullet points, numbered lists, tables and other Markdown
structure where appropriate.
Preserve the original meaning of the document, but improve its structure and readability.
Use the edit_document tool to make any changes to the document as needed.
"""

    return [
        types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=prompt
            )
        )
    ]

# Logging and Notification 

@mcp.tool(
    name="process_document",
    description="Processes a document while reporting logs and progress."
)

async def process_document(
    doc_id: str = Field(description="Id of the document to process"),
    *,
    cxt: Context
) -> str:

    if doc_id not in docs:
        raise ValueError(f"Document with id '{doc_id}' not found.")

    await cxt.info("Starting document processing...")
    await cxt.report_progress(10,100)
    await asyncio.sleep(1)

    await cxt.info("Reading document...")
    document = docs[doc_id]
    await cxt.report_progress(30, 100)
    await asyncio.sleep(1)

    await cxt.info("Analyzing document...")
    await cxt.report_progress(60, 100)
    await asyncio.sleep(1)

    await cxt.info("Preparing final result...")
    await cxt.report_progress(90, 100)
    await asyncio.sleep(1)

    await cxt.info("Document processing complete.")
    await cxt.report_progress(100, 100)

    return f"Processed document '{doc_id}': {document}"


def is_path_allowed(path: Path, roots: list[types.Root]) -> bool:
    resolved_path = path.resolve()

    for root in roots:
        root_path = Path(url2pathname(urlparse(str(root.uri)).path)).resolve()

        try:
            resolved_path.relative_to(root_path)
            return True
        except ValueError:
            continue

    return False

# Roots

@mcp.tool(
    name="list_root_documents",
    description="Lists files available inside the client's approved MCP roots."
)
async def list_root_documents(
    *,
    context: Context
) -> list[str]:
    result = await context.session.list_roots()

    files = []

    for root in result.roots:
        root_path = Path(url2pathname(urlparse(str(root.uri)).path))

        if not root_path.exists():
            continue

        for path in root_path.rglob("*"):
            if path.is_file() and is_path_allowed(path, result.roots):
                files.append(str(path))

    return files


@mcp.tool(
    name="read_root_file",
    description="Reads a file only if it is inside one of the client's approved MCP roots."
)

async def read_root_file(
    file_path: str,
    *,
    context: Context
) -> str:
    path = Path(file_path).resolve()

    result = await context.session.list_roots()

    if not is_path_allowed(path, result.roots):
        raise ValueError(
            f"Access denied: '{file_path}' is outside the client's approved MCP roots."
        )

    if not path.exists():
        raise ValueError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return path.read_text(encoding="utf-8")


# if __name__ == "__main__":
#     mcp.run()

# Temp Change 

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

