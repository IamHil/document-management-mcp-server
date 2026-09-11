from mcp.server.fastmcp import FastMCP
from pydantic import Field
from mcp import types

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





if __name__ == "__main__":
    mcp.run()

