"""Reactive Resume MCP client — connects to the RR MCP server."""

from __future__ import annotations

import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class ReactiveResumeClient:
    """Client for the Reactive Resume MCP server.

    Connects via streamable HTTP transport with x-api-key auth.
    """

    DEFAULT_URL = "http://localhost:3000/mcp"

    def __init__(self, url: str = DEFAULT_URL, api_key: str | None = None):
        self.url = url
        self.api_key = api_key or os.environ.get("RR_API_KEY", "")

    async def list_resumes(self) -> list[dict[str, Any]]:
        """List all resumes for the authenticated user."""
        async with streamablehttp_client(
            self.url, headers={"x-api-key": self.api_key}
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_resumes", {"tags": [], "sort": "lastUpdatedAt"}
                )
                return json.loads(result.content[0].text)

    async def create_resume(
        self, name: str, slug: str, tags: list[str] | None = None
    ) -> str:
        """Create a new resume and return its ID."""
        async with streamablehttp_client(
            self.url, headers={"x-api-key": self.api_key}
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "create_resume",
                    {"name": name, "slug": slug, "tags": tags or []},
                )
                data = json.loads(result.content[0].text)
                return data.get("id", data)

    async def patch_resume(
        self, resume_id: str, operations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Apply JSON Patch operations to a resume."""
        async with streamablehttp_client(
            self.url, headers={"x-api-key": self.api_key}
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "patch_resume", {"id": resume_id, "operations": operations}
                )
                return json.loads(result.content[0].text)

    async def get_resume(self, resume_id: str) -> dict[str, Any]:
        """Get full resume data by ID."""
        async with streamablehttp_client(
            self.url, headers={"x-api-key": self.api_key}
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("get_resume", {"id": resume_id})
                return json.loads(result.content[0].text)

    async def get_pdf_url(self, resume_id: str) -> dict[str, Any]:
        """Get a short-lived PDF download URL for a resume."""
        async with streamablehttp_client(
            self.url, headers={"x-api-key": self.api_key}
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "download_resume_pdf", {"id": resume_id}
                )
                return json.loads(result.content[0].text)
