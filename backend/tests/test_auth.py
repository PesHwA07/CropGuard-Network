"""Auth endpoint tests — registration, login, and token-based profile retrieval."""

import pytest


REGISTER_PAYLOAD = {
    "email": "integration@test.com",
    "password": "securepass123",
    "full_name": "Integration Tester",
    "role": "farmer",
    "district": "Chh. Sambhajinagar",
}


@pytest.mark.asyncio
async def test_register_creates_user(client):
    response = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == REGISTER_PAYLOAD["email"]
    assert data["role"] == "farmer"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_returns_token(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/api/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post(
        "/api/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrongpass"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client):
    await client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    token = login_resp.json()["access_token"]
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == REGISTER_PAYLOAD["email"]


@pytest.mark.asyncio
async def test_me_without_token_returns_401(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
