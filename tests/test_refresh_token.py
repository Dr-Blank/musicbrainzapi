from unittest.mock import Mock, patch

import pytest
from requests import HTTPError, Response

from musicbrainzapi.api import UserAPI


def test_token_refresh(mock_api: UserAPI):
    # set a callback to refresh the token
    refresh_called = False

    def refresh_token():
        nonlocal refresh_called
        refresh_called = True
        return "new_token"

    mock_api._refresh_callback = refresh_token

    # mock the response from the server
    mock_error = HTTPError(response=Response())
    mock_error.response.status_code = 401

    mock_api._session.request.side_effect = mock_error

    # make a request
    with pytest.raises(Exception):
        mock_api.get_collections()

    # assert that the token was refreshed
    assert refresh_called
