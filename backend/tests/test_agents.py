from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database.base import Base
from app.database.session import engine
from app.main import app


def test_list_agents_returns_seeded_demo_agent_without_sensitive_fields():
    connection = engine.connect()
    Base.metadata.create_all(bind=connection)
    session = Session(bind=connection)

    def get_test_db():
        yield session

    app.dependency_overrides[get_db] = get_test_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/agents")

        assert response.status_code == 200
        agents = response.json()
        assert any(agent["name"] == "SwarVox Appointment Assistant" for agent in agents)

        agent = next(agent for agent in agents if agent["name"] == "SwarVox Appointment Assistant")
        assert "system_instructions" not in agent
        assert "allowed_tools" not in agent
        assert "escalation_number" not in agent
    finally:
        app.dependency_overrides.clear()
        session.close()
        Base.metadata.drop_all(bind=connection)
        connection.close()
