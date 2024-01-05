from musicbrainzapi import UserAPI
import re

def test_header_auth():
    api = UserAPI("token")
    header = api._session.headers.pop("Authorization")
    assert header == "Bearer token"


def test_header_user_agent():
    api = UserAPI("token")
    header = api._session.headers.pop("User-Agent")
    assert re.match(r"^musicbrainzapi/\d+\.\d+\.\d+ \(.*\)", header)