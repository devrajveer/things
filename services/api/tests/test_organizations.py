import pytest
from httpx import AsyncClient
from yp_api.models.auth import Organization, OrganizationMember

@pytest.fixture
async def create_org(db_session, test_user):
    # This is a helper fixture, assuming db_session and test_user exist
    pass

@pytest.mark.asyncio
async def test_list_organizations(client: AsyncClient, auth_headers):
    response = await client.get("/v1/organizations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 1  # Should at least have the Personal org

@pytest.mark.asyncio
async def test_create_organization(client: AsyncClient, auth_headers):
    payload = {"name": "Test Org"}
    response = await client.post("/v1/organizations", json=payload, headers=auth_headers)
    assert response.status_code == 201
    
    data = response.json()["data"]
    assert data["name"] == "Test Org"
    assert data["tier"] == "free"
    assert "id" in data

@pytest.mark.asyncio
async def test_update_organization(client: AsyncClient, auth_headers):
    # Create org first
    payload = {"name": "To Update"}
    create_res = await client.post("/v1/organizations", json=payload, headers=auth_headers)
    org_id = create_res.json()["data"]["id"]

    # Update org
    update_payload = {"name": "Updated Name"}
    response = await client.patch(f"/v1/organizations/{org_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_delete_organization(client: AsyncClient, auth_headers):
    # Create org first
    payload = {"name": "To Delete"}
    create_res = await client.post("/v1/organizations", json=payload, headers=auth_headers)
    org_id = create_res.json()["data"]["id"]

    # Delete org
    response = await client.delete(f"/v1/organizations/{org_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify deleted
    get_res = await client.get(f"/v1/organizations/{org_id}", headers=auth_headers)
    assert get_res.status_code == 404
