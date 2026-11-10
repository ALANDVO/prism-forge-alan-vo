"""MCP Server implementation for agent memory system."""

import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    CallToolRequest,
)
import mcp.types as types

from app.models.agent import Agent
from app.services.agent_service import AgentService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


# Global instance placeholder - will be initialized in main.py
mcp_server: Optional["MCPServer"] = None


@dataclass
class MemoryEntry:
    """Represents a single memory entry in the agent's memory."""
    key: str
    value: str
    agent_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class MCPServer:
    """MCP Server that exposes agent memory tools via MCP protocol."""

    def __init__(self, session_factory):
        """Initialize MCP server with database session factory."""
        self.session_factory = session_factory
        self.server = Server("prism-forge-memory")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP request handlers."""

        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List available memory tools."""
            return ListToolsResult(tools=[
                Tool(
                    name="memory_read",
                    description="Read a memory entry for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "integer", "description": "Agent ID"},
                            "key": {"type": "string", "description": "Memory key to read"},
                        },
                        "required": ["agent_id", "key"],
                    },
                ),
                Tool(
                    name="memory_write",
                    description="Write a memory entry for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "integer", "description": "Agent ID"},
                            "key": {"type": "string", "description": "Memory key"},
                            "value": {"type": "string", "description": "Memory value to store"},
                        },
                        "required": ["agent_id", "key", "value"],
                    },
                ),
                Tool(
                    name="memory_list",
                    description="List all memory keys for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "integer", "description": "Agent ID"},
                        },
                        "required": ["agent_id"],
                    },
                ),
                Tool(
                    name="memory_delete",
                    description="Delete a memory entry for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_id": {"type": "integer", "description": "Agent ID"},
                            "key": {"type": "string", "description": "Memory key to delete"},
                        },
                        "required": ["agent_id", "key"],
                    },
                ),
            ])

        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Handle tool calls from MCP clients."""
            name = request.params.name
            arguments = request.params.arguments or {}
            try:
                if name == "memory_read":
                    return await self._handle_memory_read(arguments)
                elif name == "memory_write":
                    return await self._handle_memory_write(arguments)
                elif name == "memory_list":
                    return await self._handle_memory_list(arguments)
                elif name == "memory_delete":
                    return await self._handle_memory_delete(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True,
                    )
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True,
                )

        self.server.add_request_handler("tools/list", ListToolsRequest, handle_list_tools)
        self.server.add_request_handler("tools/call", CallToolRequest, handle_call_tool)

    async def _handle_memory_read(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle memory read tool call."""
        agent_id = arguments.get("agent_id")
        key = arguments.get("key")

        if not isinstance(agent_id, int) or not isinstance(key, str):
            return CallToolResult(
                content=[TextContent(type="text", text="Invalid arguments: agent_id must be int, key must be string")],
                isError=True,
            )

        async with self.session_factory() as session:
            service = AgentService(session)
            agent = await service.get_agent(agent_id)
            if not agent:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Agent {agent_id} not found")],
                    isError=True,
                )

            # Read from agent's workspace memory file
            try:
                memory_path = f".memory/{key}.json"
                content = await service.read_file(agent_id, memory_path)
                memory_data = json.loads(content)
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(memory_data, indent=2))],
                )
            except FileNotFoundError:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Memory key '{key}' not found for agent {agent_id}")],
                    isError=True,
                )
            except json.JSONDecodeError:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Invalid memory data for key '{key}'")],
                    isError=True,
                )

    async def _handle_memory_write(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle memory write tool call."""
        agent_id = arguments.get("agent_id")
        key = arguments.get("key")
        value = arguments.get("value")

        if not isinstance(agent_id, int) or not isinstance(key, str) or not isinstance(value, str):
            return CallToolResult(
                content=[TextContent(type="text", text="Invalid arguments: agent_id must be int, key and value must be strings")],
                isError=True,
            )

        async with self.session_factory() as session:
            service = AgentService(session)
            agent = await service.get_agent(agent_id)
            if not agent:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Agent {agent_id} not found")],
                    isError=True,
                )

            memory_data = {
                "key": key,
                "value": value,
                "agent_id": agent_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            memory_path = f".memory/{key}.json"
            await service.write_file(agent_id, memory_path, json.dumps(memory_data, indent=2))

            return CallToolResult(
                content=[TextContent(type="text", text=f"Memory key '{key}' written for agent {agent_id}")],
            )

    async def _handle_memory_list(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle memory list tool call."""
        agent_id = arguments.get("agent_id")

        if not isinstance(agent_id, int):
            return CallToolResult(
                content=[TextContent(type="text", text="Invalid arguments: agent_id must be int")],
                isError=True,
            )

        async with self.session_factory() as session:
            service = AgentService(session)
            agent = await service.get_agent(agent_id)
            if not agent:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Agent {agent_id} not found")],
                    isError=True,
                )

            try:
                files = await service.list_files(agent_id, ".memory")
                keys = [f["name"].replace(".json", "") for f in files if f["name"].endswith(".json")]
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({"keys": keys}, indent=2))],
                )
            except FileNotFoundError:
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps({"keys": []}, indent=2))],
                )

    async def _handle_memory_delete(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle memory delete tool call."""
        agent_id = arguments.get("agent_id")
        key = arguments.get("key")

        if not isinstance(agent_id, int) or not isinstance(key, str):
            return CallToolResult(
                content=[TextContent(type="text", text="Invalid arguments: agent_id must be int, key must be string")],
                isError=True,
            )

        async with self.session_factory() as session:
            service = AgentService(session)
            agent = await service.get_agent(agent_id)
            if not agent:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Agent {agent_id} not found")],
                    isError=True,
                )

            memory_path = f".memory/{key}.json"
            try:
                # Check if file exists first
                await service.read_file(agent_id, memory_path)
                # Delete by writing empty content (workspace doesn't have delete_file yet)
                # We'll need to implement proper delete or use a workaround
                import os
                workspace_root = service._resolve_workspace_root(agent)
                target = service._validate_path_within_workspace(agent, memory_path)
                target.unlink(missing_ok=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Memory key '{key}' deleted for agent {agent_id}")],
                )
            except FileNotFoundError:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Memory key '{key}' not found for agent {agent_id}")],
                    isError=True,
                )

    async def run_stdio(self) -> None:
        """Run the MCP server over stdio."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="prism-forge-memory",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


if __name__ == "__main__":
    import asyncio
    from app.core.database import init_db, get_async_session_factory

    async def main():
        await init_db()
        server = MCPServer(get_async_session_factory())
        await server.run_stdio()

    asyncio.run(main())
