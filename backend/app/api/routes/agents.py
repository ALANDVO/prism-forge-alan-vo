from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db_session
from app.services.agent_service import AgentService, WorkspaceError
from app.core.security import get_current_user, User

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    name: str = Field(..., min_length=1, max_length=255)
    workspace_path: str = Field(..., min_length=1, max_length=512)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config_json: Optional[str] = None


class AgentUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_config_json: Optional[str] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    workspace_path: str
    system_prompt: Optional[str]
    model_config: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
class AgentListResponse(BaseModel):
    agents: list[AgentResponse]
    total: int


class FileReadResponse(BaseModel):
    path: str
    content: str


class FileWriteRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str


class FileWriteResponse(BaseModel):
    path: str
    size: int


class FileListResponse(BaseModel):
    files: list[dict]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    service = AgentService(session)
    try:
        agent = await service.create_agent(
            name=data.name,
            workspace_path=data.workspace_path,
            description=data.description,
            system_prompt=data.system_prompt,
            model_config=data.model_config_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AgentResponse.model_validate(agent)


@router.get("", response_model=AgentListResponse)
async def list_agents(
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AgentListResponse:
    service = AgentService(session)
    agents = await service.list_agents(active_only=active_only)
    return AgentListResponse(
        agents=[AgentResponse.model_validate(a) for a in agents],
        total=len(agents),
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    service = AgentService(session)
    agent = await service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    data: AgentUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AgentResponse:
    service = AgentService(session)
    try:
        agent = await service.update_agent(
            agent_id=agent_id,
            name=data.name,
            description=data.description,
            system_prompt=data.system_prompt,
            model_config=data.model_config_json,
            is_active=data.is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    service = AgentService(session)
    deleted = await service.delete_agent(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/{agent_id}/files", response_model=FileListResponse)
async def list_agent_files(
    agent_id: int,
    path: str = Query("", description="Relative path within workspace"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileListResponse:
    service = AgentService(session)
    try:
        files = await service.list_files(agent_id, path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkspaceError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return FileListResponse(files=files)


@router.get("/{agent_id}/files/read", response_model=FileReadResponse)
async def read_agent_file(
    agent_id: int,
    path: str = Query(..., description="Relative path within workspace"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileReadResponse:
    service = AgentService(session)
    try:
        content = await service.read_file(agent_id, path)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkspaceError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FileReadResponse(path=path, content=content)


@router.post("/{agent_id}/files/write", response_model=FileWriteResponse)
async def write_agent_file(
    agent_id: int,
    data: FileWriteRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileWriteResponse:
    service = AgentService(session)
    try:
        target = await service.write_file(agent_id, data.path, data.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except WorkspaceError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return FileWriteResponse(path=data.path, size=len(data.content.encode("utf-8")))