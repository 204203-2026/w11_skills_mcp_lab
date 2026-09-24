def test_home(client):
    assert client.get("/").json()["app"] == "TeamBoard"


def test_login_and_bad_password(client):
    response = client.post("/login", json={"name": "Alice", "password": "alice-lab"})
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"
    assert client.post("/login", json={"name": "Alice", "password": "wrong"}).status_code == 401


def test_cards(client):
    response = client.post("/cards", json={"board_id": 1, "title": "Test", "status": "todo"})
    assert response.status_code == 201
    assert client.get(f"/cards/{response.json()['id']}").json()["title"] == "Test"
