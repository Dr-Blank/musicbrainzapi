from unittest.mock import Mock

import pytest

from musicbrainzapi.api import BASE_URL, UserAPI, WSEndpoint


# test if client parameters are set correctly when submitting a rating
def test_submit_rating(mock_api: UserAPI):
    mock_session = mock_api._session
    my_rating = {"artist": {"someid": 100}}
    mock_api._get_ratings_dict = Mock(return_value="some xml")
    mock_api.submit_ratings(my_rating)

    mock_session.request.assert_called_once_with(
        "POST",
        f"{BASE_URL}{WSEndpoint.RATING.value}",
        params={"client": mock_api._client_name},
        headers={"Content-Type": "application/xml; charset=UTF-8"},
        data="some xml",
    )


def test_invalid_rating(mock_api: UserAPI):
    my_rating = {"invalid": {"someid": 100}}
    with pytest.raises(ValueError):
        mock_api.submit_ratings(my_rating)
