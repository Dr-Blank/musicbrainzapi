from unittest.mock import Mock
import pytest

from musicbrainzapi.api import UserAPI

client_name = "Ampulse"
client_version = "0.1.0"
token_name = "token"


# add variables to pytest namespace
def pytest_configure():
    pytest.client_name = client_name
    pytest.client_version = client_version
    pytest.token_name = token_name


# a pytest fixture to yield a UserAPI instance throughout the tests
@pytest.fixture()
def api():
    api = UserAPI(
        auth_token=token_name,
        client_name=client_name,
        client_version=client_version,
    )
    yield api


@pytest.fixture()
def mock_api(api):
    mock_session = Mock()
    api._session = mock_session
    yield api
