import re

import pytest

from musicbrainzapi import UserAPI


def test_header_authorization(api: UserAPI):
    header = api._session.headers.pop("Authorization")
    assert header == f"Bearer {pytest.token_name}"


def test_header_user_agent(api: UserAPI):
    header = str(api._session.headers.pop("User-Agent"))
    assert re.match(
        rf"^{pytest.client_name}/{pytest.client_version} musicbrainzapi/\d+\.\d+\.\d+"
        r" \(.*\)$",
        header,
    )
