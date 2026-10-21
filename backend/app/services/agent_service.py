from pathlib import Path
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.core.config import get_settings


class WorkspaceError(Exception):
    """Raised when workspace operations violate isolation."""


class AgentService:
    """Business logic for agent management with strict workspace isolation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    def _resolve_workspace_root(self, agent: Agent) -> Path:
        """Resolve the absolute workspace root for an agent."""
        base = Path(self.settings.database_url.replace("sqlite+aiosqlite:///", "")).parent / "workspaces"
        return (base / agent.workspace_path.lstrip("./")).resolve()

    def _validate_path_within_workspace(self, agent: Agent, target_path: str) -> Path:
        """
        Validate that a target path is within the agent's workspace.
        Raises WorkspaceError if path escapes the workspace.
        """
        workspace_root = self._resolve_workspace_root(agent)
        target = (workspace_root / target_path).resolve()

        # Check if target is within workspace_root
        try:
            target.relative_to(workspace_root)
        except ValueError:
            raise WorkspaceError(
                f"Path '{target_path}' escapes agent workspace '{agent.workspace_path}'"
            )

        return target

    async def create_agent(
        self,
        name: str,
        workspace_path: str,
        description: str | None = None,
        system_prompt: str | None = None,
        model_config: str | None = None,
    ) -> Agent:
        """Create a new agent with its own isolated workspace."""
        # Check name uniqueness
        existing = await self.session.execute(select(Agent).where(Agent.name == name))
        if existing.scalar_one_or_none():
            raise ValueError(f"Agent with name '{name}' already exists")

        agent = Agent(
            name=name,
            workspace_path=workspace_path,
            description=description,
            system_prompt=system_prompt,
            model_config=model_config or "{}",
            is_active=True,
        )
        self.session.add(agent)
        await self.session.flush()

        # Create workspace directory
        workspace_root = self._resolve_workspace_root(agent)
        workspace_root.mkdir(parents=True, exist_ok=True)

        return agent

    async def get_agent(self, agent_id: int) -> Optional[Agent]:
        result = await self.session.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def get_agent_by_name(self, name: str) -> Optional[Agent]:
        result = await self.session.execute(select(Agent).where(Agent.name == name))
        return result.scalar_one_or_none()

    async def list_agents(self, active_only: bool = True) -> list[Agent]:
        query = select(Agent)
        if active_only:
            query = query.where(Agent.is_active)
        query = query.order_by(Agent.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_agent(
        self,
        agent_id: int,
        name: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
        model_config: str | None = None,
        is_active: bool | None = None,
    ) -> Optional[Agent]:
        agent = await self.get_agent(agent_id)
        if not agent:
            return None

        if name is not None:
            # Check uniqueness
            existing = await self.session.execute(
                select(Agent).where(Agent.name == name, Agent.id != agent_id)
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Agent with name '{name}' already exists")
            agent.name = name

        if description is not None:
            agent.description = description
        if system_prompt is not None:
            agent.system_prompt = system_prompt
        if model_config is not None:
            agent.model_config = model_config
        if is_active is not None:
            agent.is_active = is_active

        await self.session.flush()
        return agent

    async def delete_agent(self, agent_id: int) -> bool:
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        await self.session.delete(agent)
        return True

    async def read_file(self, agent_id: int, path: str) -> str:
        """Read a file from agent's workspace."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        target = self._validate_path_within_workspace(agent, path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not target.is_file():
            raise ValueError(f"Not a file: {path}")

        return target.read_text(encoding="utf-8")

    async def write_file(self, agent_id: int, path: str, content: str) -> Path:
        """Write a file to agent's workspace (strict isolation)."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        target = self._validate_path_within_workspace(agent, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    async def list_files(self, agent_id: int, path: str = "") -> list[dict]:
        """List files in agent's workspace."""
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        target = self._validate_path_within_workspace(agent, path)
        if not target.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        if target.is_file():
            return [{"name": target.name, "path": path, "is_dir": False}]

        entries = []
        for entry in target.iterdir():
            rel_path = entry.relative_to(self._resolve_workspace_root(agent))
            entries.append(
                {
                    "name": entry.name,
                    "path": str(rel_path),
                    "is_dir": entry.is_dir(),
                }
            )
        return entries