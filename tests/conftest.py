# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from typing import Generator, Dict

from app.main import app
from app.services.operator_runner import OperatorRunnerInterface
from app.infrastructure.playwright_manager import BrowserManagerInterface
from app.infrastructure.ai_client import AIClientInterface

# Fixture for FastAPI test client
@pytest.fixture
def client() -> Generator:
    with TestClient(app) as c:
        yield c

# Fixture for test data
@pytest.fixture
def sample_html_snapshot() -> str:
    with open("tests/test_data/snapshots/example_page.html", "r") as f:
        return f.read()

@pytest.fixture
def sample_test_case() -> str:
    with open("tests/test_data/test_cases/sample_test_case.txt", "r") as f:
        return f.read()

# Mock fixtures
@pytest.fixture
def mock_test_runner(mocker):
    return mocker.Mock(spec=OperatorRunnerInterface)

@pytest.fixture
def mock_browser_manager(mocker):
    return mocker.Mock(spec=BrowserManagerInterface)

@pytest.fixture
def mock_ai_client(mocker):
    return mocker.Mock(spec=AIClientInterface)