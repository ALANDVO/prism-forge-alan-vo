import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, db_session: AsyncSession):
    """Test creating an agent via API."""
    response = await client.post(
        "/api/agents",
        json={
            "name": "Test Agent",
            "workspace_path": "./test-agent",
            "description": "A test agent",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["workspace_path"] == "./test-agent"
    assert data["description"] == "A test agent"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_agent_duplicate_name_fails(client: AsyncClient):
    """Test that duplicate agent names are rejected."""
    # Create first agent
    await client.post(
        "/api/agents",
        json={"name": "Duplicate", "workspace_path": "./agent-1"},
    )
    # Try to create second with same name
    response = await client.post(
        "/api/agents",
        json={"name": "Duplicate", "workspace_path": "./agent-2"},
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    """Test listing agents."""
    # Create a couple agents
    await client.post("/api/agents", json={"name": "Agent A", "workspace_path": "./a"})
    await client.post("/api/agents", json={"name": "Agent B", "workspace_path": "./b"})

    response = await client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    # Total includes agents from previous tests (test_create_agent, test_create_agent_duplicate_name_fails, etc.)
    assert data["total"] >= 2
    assert len(data["agents"]) >= 2
    names = {a["name"] for a in data["agents"]}
    assert "Agent A" in names
    assert "Agent B" in names


@pytest.mark.asyncio
async def test_get_agent(client: AsyncClient):
    """Test getting a single agent."""
    create_resp = await client.post(
        "/api/agents",
        json={"name": "Get Me", "workspace_path": "./get-me"},
    )
    agent_id = create_resp.json()["id"]

    response = await client.get(f"/api/agents/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "Get Me"


@pytest.mark.asyncio
async def test_get_nonexistent_agent(client: AsyncClient):
    """Test 404 for nonexistent agent."""
    response = await client.get("/api/agents/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client: AsyncClient):
    """Test updating an agent."""
    create_resp = await client.post(
        "/api/agents",
        json={"name": "Original", "workspace_path": "./orig"},
    )
    agent_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/agents/{agent_id}",
        json={"name": "Updated", "description": "New description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["description"] == "New description"


@pytest.mark.asyncio
async def test_delete_agent(client: AsyncClient):
    """Test deleting an agent."""
    create_resp = await client.post(
        "/api/agents",
        json={"name": "To Delete", "workspace_path": "./delete-me"},
    )
    agent_id = create_resp.json()["id"]

    response = await client.delete(f"/api/agents/{agent_id}")
    assert response.status_code == 204

    # Verify deleted
    get_resp = await client.get(f"/api/agents/{agent_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_agent_workspace_isolation(client: AsyncClient):
    """Test that agents cannot access each other's workspaces."""
    # Create two agents
    a1 = await client.post("/api/agents", json={"name": "Agent1", "workspace_path": "./agent1"})
    a2 = await client.post("/api/agents", json={"name": "Agent2", "workspace_path": "./agent2"})
    id1 = a1.json()["id"]
    id2 = a2.json()["id"]

    # Agent 1 writes a file
    await client.post(
        f"/api/agents/{id1}/files/write",
        json={"path": "secret.txt", "content": "Agent 1 secret"},
    )

    # Agent 1 reads its own file - should succeed
    read1 = await client.get(f"/api/agents/{id1}/files/read", params={"path": "secret.txt"})
    assert read1.status_code == 200
    assert read1.json()["content"] == "Agent 1 secret"

    # Agent 2 tries to read Agent 1's file - should fail with 403
    read2 = await client.get(f"/api/agents/{id2}/files/read", params={"path": "../agent1/secret.txt"})
    assert read2.status_code == 403
    assert "escapes" in read2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_agent_file_operations(client: AsyncClient):
    """Test file read/write/list operations within workspace."""
    create_resp = await client.post(
        "/api/agents",
        json={"name": "File Agent", "workspace_path": "./file-agent"},
    )
    agent_id = create_resp.json()["id"]

    # Write a file
    write_resp = await client.post(
        f"/api/agents/{agent_id}/files/write",
        json={"path": "notes/note1.txt", "content": "Hello world"},
    )
    assert write_resp.status_code == 200

    # Read the file
    read_resp = await client.get(
        f"/api/agents/{agent_id}/files/read",
        params={"path": "notes/note1.txt"},
    )
    assert read_resp.status_code == 200
    assert read_resp.json()["content"] == "Hello world"

    # List files
    list_resp = await client.get(f"/api/agents/{agent_id}/files", params={"path": "notes"})
    assert list_resp.status_code == 200
    files = list_resp.json()["files"]
    assert len(files) == 1
    assert files[0]["name"] == "note1.txt"
    assert files[0]["is_dir"] is False