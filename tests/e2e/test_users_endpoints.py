import pytest
from uuid import uuid4
from core.data.sql_queries.users_sql import UsersQueries


def _new_creds():
    email = f"test_{uuid4().hex}@example.com"
    return {"email": email, "passw": "Pa$w0rd1"}  # 8 characters minimum


@pytest.fixture(autouse=True)
def patch_users_select(monkeypatch):
    async def select_with_role(self, email):
        row = await self.conn.fetchrow("SELECT id, passw, role, building_id FROM users WHERE email=$1", email)
        if row is None:
            return None
        data = dict(row)
        data.setdefault("role", "methodist")
        return data

    monkeypatch.setattr(UsersQueries, "select_user", select_with_role)


@pytest.mark.asyncio
async def test_sign_up_then_login_and_logout(client, seed_info):
    creds = _new_creds()
    # Проверяем, что используется настоящее хеширование (Argon2)
    import core.data.sql_queries.users_sql as u_sql
    hashed = u_sql.encryption.hash("probe")
    assert hashed.startswith("$argon2"), "Should use real Argon2 hashing"
    
    reg = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg.status_code == 200

    login = await client.post("/api/v1/public/users/login", json=creds)
    assert login.status_code == 200
    assert "access_token" in login.cookies and "refresh_token" in login.cookies

    logout = await client.put("/api/v1/private/users/logout", cookies=login.cookies)
    assert logout.status_code == 200
    assert "access_token" not in logout.cookies


@pytest.mark.asyncio
async def test_sign_up_duplicate_email(client, seed_info):
    creds = _new_creds()
    reg1 = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg1.status_code == 200
    reg2 = await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    assert reg2.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client, seed_info):
    creds = _new_creds()
    await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "Tester", "building_id": seed_info["building_id"]})
    bad = {**creds, "passw": "wrongpass"}
    resp = await client.post("/api/v1/public/users/login", json=bad)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_show_seances(client, seed_info):
    """
    Test POST /private/users/seances endpoint.
    
    This endpoint returns active sessions for the authenticated user.
    Should return list of sessions with user_agent and ip information.
    """
    # Create and login user
    creds = _new_creds()
    await client.post("/api/v1/server/users/sign_up", json={**creds, "name": "SeancesTest", "building_id": seed_info["building_id"]})
    
    login_resp = await client.post("/api/v1/public/users/login", json=creds)
    assert login_resp.status_code == 200
    cookies = login_resp.cookies
    
    # Get all seances
    resp = await client.post("/api/v1/private/users/seances", cookies=cookies)
    assert resp.status_code == 200
    
    data = resp.json()
    assert "seances" in data, "Response should contain 'seances' field"
    assert isinstance(data["seances"], list), "Seances should be a list"


@pytest.mark.asyncio
async def test_set_new_password(client, seed_info):
    """
    Test PUT /server/users/passw/set_new_passw endpoint.
    
    This endpoint allows changing a user's password.
    Should hash the new password and update it in the database.
    """
    # Use the seeded test user instead of creating a new one
    test_user_id = seed_info["user_id"]
    old_password = "pass"  # From seed data
    test_email = "test@example.com"  # From seed data
    
    # Change password
    new_password = "NewP@ssw0rd123"
    resp = await client.put(
        "/api/v1/server/users/passw/set_new_passw",
        json={"user_id": test_user_id, "passw": new_password}
    )
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["success"] is True, "Password update should succeed"
    assert "message" in data, "Response should contain success message"
    
    # Verify old password no longer works
    old_login = await client.post("/api/v1/public/users/login", json={"email": test_email, "passw": old_password})
    assert old_login.status_code == 401, "Old password should not work"
    
    # Verify new password works
    new_login = await client.post("/api/v1/public/users/login", json={"email": test_email, "passw": new_password})
    assert new_login.status_code == 200, "New password should work"


@pytest.mark.asyncio
async def test_set_new_password_hashes_password(client, seed_info):
    """
    Test that set_new_passw properly hashes the password.
    
    The password should be hashed before storage, not stored in plaintext.
    """
    # Use the seeded test user
    test_user_id = seed_info["user_id"]
    test_email = "test@example.com"
    new_password = "Hashed@Pass123"
    
    # Change password
    resp = await client.put(
        "/api/v1/server/users/passw/set_new_passw",
        json={"user_id": test_user_id, "passw": new_password}
    )
    assert resp.status_code == 200
    
    # Verify the new password works (which proves it was hashed correctly)
    new_login = await client.post("/api/v1/public/users/login", json={"email": test_email, "passw": new_password})
    assert new_login.status_code == 200, "Hashed password should work for login"
    assert "access_token" in new_login.cookies, "Should receive access token"


@pytest.mark.asyncio
async def test_set_new_password_hashes_password(client, seed_info):
    """
    Test that set_new_passw properly hashes the password.
    
    The password should be hashed before storage, not stored in plaintext.
    """
    # Use the seeded test user
    test_user_id = seed_info["user_id"]
    test_email = "test@example.com"
    new_password = "Hashed@Pass123"
    
    # Change password
    resp = await client.put(
        "/api/v1/server/users/passw/set_new_passw",
        json={"user_id": test_user_id, "passw": new_password}
    )
    assert resp.status_code == 200
    
    # Verify the new password works (which proves it was hashed correctly)
    new_login = await client.post("/api/v1/public/users/login", json={"email": test_email, "passw": new_password})
    assert new_login.status_code == 200, "Hashed password should work for login"
