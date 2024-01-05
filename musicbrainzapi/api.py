""" API for musicbrainz"""
import importlib.metadata
from enum import Enum
from http import HTTPStatus
from typing import Any, Callable, Dict, Optional, cast

import requests
from requests_ratelimiter import LimiterSession
from .exceptions import (
    APIError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

__all__ = ["UserAPI"]



BASE_URL = "https://musicbrainz.org/ws/2"

class Endpoint(Enum):
    rating = "/rating"
    tags = "/tag"
    collection = "/collection"



class UserAPI:
    """
    API for musicbrainz

    .. note::
        The API is rate limited to 1 request per second

    Parameters
    ---------
    auth_token: str
        The authentication token for the user
    base_url: str
        The base url for the API
    session: requests.Session
        The session to use for the API
        must limit the number of requests per second
    refresh_callback: Callable[..., str]
        A callback function to refresh the auth_token
        if it expires
    """
    def __init__(
        self,
        auth_token: str,
        base_url: str = BASE_URL,
        session: Optional[requests.Session] = None,
        refresh_callback: Optional[Callable[..., str]] = None,
    ):
        self._base_url = base_url or BASE_URL
        self._session = cast(requests.Session, session or LimiterSession(per_second=1))
        _app_name = __name__.split(".")[0]
        app_metadata = importlib.metadata.metadata(_app_name)

        self._session.headers.update({"Authorization": f"Bearer {auth_token}"})
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update({"User-Agent": f"{_app_name}/{app_metadata['Version']} ( {app_metadata['Home-page']} )"})
        
        self._refresh_callback = refresh_callback




    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        url = self._base_url + endpoint

        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            response = exc.response
            if not response:
                raise exc
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise NotFoundError(response) from exc
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError(response) from exc
            if 500 <= response.status_code < 600:
                raise ServerError(response) from exc
            raise APIError(response) from exc
        return response.json()
    
    def get_rating(
        self,
        mbid: str,
        type: str,
    ):
        """
        Get rating for a given MBID
        """
        endpoint = Endpoint.rating.value
        response = self._make_request("GET", endpoint, params={"mbid": mbid, "type": type})
        return response
    
    def get_collections(
        self,
    ):
        """
        Get collection for the user
        """
        endpoint = Endpoint.collection.value
        response = self._make_request("GET", endpoint)
        return response