""" API for musicbrainz"""

import importlib.metadata
from enum import Enum
from http import HTTPStatus
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

import requests
from bs4 import BeautifulSoup, Tag
from musicbrainzngs import mbxml
from requests import Response
from requests_ratelimiter import LimiterSession

from musicbrainzapi.models import MBEntity

from .enums import RATING_SUPPORTED_ENTITIES, CoreEntities
from .exceptions import (
    APIError,
    NotFoundError,
    RateLimitError,
    ServerError,
    UnsupportedEntityError,
)

__all__ = ["UserAPI"]

logger = getLogger(__name__)

BASE_URL = "https://musicbrainz.org"


MBId = TypeVar("MBId", bound=str)
"""A MusicBrainz Identifier"""


Rating = TypeVar("Rating", bound=int)
"""A rating for a resource

is an integer between 0 and 100

.. note::
    0 is a special value that means "no vote"
"""


class WebEndpoints(str, Enum):
    """endpoints for the web, not from the API"""

    RATING = "/user/{user_name}/ratings/{mb_type}"


class WSEndpoint(str, Enum):
    """Endpoints for the API"""

    RATING = "/ws/2/rating"
    TAG = "/ws/2/tag"
    COLLECTION = "/ws/2/collection"


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
        client_name: str,
        client_version: str,
        base_url: str = BASE_URL,
        session: Optional[requests.Session] = None,
        refresh_callback: Optional[Callable[..., str]] = None,
    ):
        self._base_url = base_url or BASE_URL
        self._session = cast(
            requests.Session, session or LimiterSession(per_second=1)
        )
        _app_name = __name__.split(".", 1)[0]
        app_metadata = importlib.metadata.metadata(_app_name)

        self._client_name = f"{client_name}-{client_version}"
        self._session.headers.update({"Authorization": f"Bearer {auth_token}"})
        self._session.headers.update({"Accept": "application/json"})
        self._session.headers.update(
            {
                "User-Agent": (
                    f"{client_name}/{client_version} "
                    f"{_app_name}/{app_metadata['Version']} ("
                    f" {app_metadata['Home-page']} )"
                )
            }
        )

        self._refresh_callback = refresh_callback

    def _make_request(
        self,
        method: str,
        endpoint: str,
        tries_left: int = 1,
        **kwargs: Any,
    ) -> Response:
        url = (
            self._base_url + endpoint if endpoint.startswith("/") else endpoint
        )
        logger.debug("%s request to %s with %s", method, url, kwargs)

        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            response = exc.response
            if response is None:
                raise exc
            if response.status_code == HTTPStatus.UNAUTHORIZED:
                if self._refresh_callback is None:
                    raise exc
                if tries_left <= 0:
                    raise exc
                # refresh the token
                self._session.headers.update(
                    {"Authorization": f"Bearer {self._refresh_callback()}"}
                )
                # retry the request
                logger.debug("retrying request with refreshed token")
                return self._make_request(
                    method, endpoint, tries_left - 1, **kwargs
                )
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise NotFoundError(response) from exc
            if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                raise RateLimitError(response) from exc
            if 500 <= response.status_code < 600:
                raise ServerError(response) from exc
            raise APIError(response) from exc
        return response

    def _make_post_request(
        self,
        endpoint: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # add client string to params
        kwargs["params"] = kwargs.get("params", {})
        kwargs["params"].update({"client": self._client_name})
        # also set the content type as xml
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"].update(
            {"Content-Type": "application/xml; charset=UTF-8"}
        )

        logger.debug("special post request with %s", kwargs)
        return self._make_request("POST", endpoint, **kwargs).json()

    def _get_ratings_entities(
        self, ratings: List[BeautifulSoup]
    ) -> List[MBEntity]:
        """Get the entities for the ratings"""
        links: List[MBEntity] = []
        for rating in ratings:
            int_rating = float(rating.text) * 20
            link = rating.find_next("a")
            if link is None or not isinstance(link, Tag):
                raise ValueError("No link found in rating")

            _, entity, mbid = link.attrs["href"].split("/")
            entity_name = link.findChild().text if link.findChild() else None  # type: ignore
            links.append(
                MBEntity(
                    mbid=mbid,
                    mb_type=CoreEntities(entity),
                    name=entity_name,
                    rating=int_rating,
                )
            )
        return links

    def _parse_ratings(self, ratings_soup: BeautifulSoup) -> List[MBEntity]:
        """Parse a ratings from a BeautifulSoup object"""
        ratings = ratings_soup.find_all("span", class_="current-rating")
        return self._get_ratings_entities(ratings)

    def _get_soup(self, endpoint: str) -> BeautifulSoup:
        """Get the soup for an endpoint"""
        response = self._make_request("GET", endpoint)
        return BeautifulSoup(response.text, "html.parser")

    def _soup_next_page_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Get the next page from a soup"""
        pagination_ul = soup.find("ul", class_="pagination")
        if pagination_ul is None or not isinstance(pagination_ul, Tag):
            return None
        next_page = pagination_ul.find("li", text="Next").find("a")  # type: ignore
        if next_page is None or not isinstance(next_page, Tag):
            return None
        next_page_link = next_page["href"]
        return str(next_page_link)

    def get_ratings(
        self,
        user_name: str,
        mb_type: str,
    ):
        """
        Get ratings of a user for a type of entity
        """
        if mb_type not in RATING_SUPPORTED_ENTITIES:
            raise UnsupportedEntityError(mb_type, RATING_SUPPORTED_ENTITIES)

        endpoint = WebEndpoints.RATING.value.format(
            user_name=user_name, mb_type=mb_type.replace("-", "_")
        )
        soup = self._get_soup(endpoint)
        next_link = self._soup_next_page_link(soup)
        ratings = self._parse_ratings(soup)
        while next_link is not None:
            soup = self._get_soup(next_link)
            next_link = self._soup_next_page_link(soup)
            ratings.extend(self._parse_ratings(soup))
        return ratings

    def get_collections(
        self,
    ):
        """
        Get collection for the user
        """
        endpoint = WSEndpoint.COLLECTION.value
        response = self._make_request("GET", endpoint)
        return response.json()

    def _get_ratings_dict(
        self,
        entity_ratings: Dict[str, Dict[MBId, Rating]],
    ):
        """Get the ratings dict for the mbxml module"""
        rating_dict = {
            f"{entity}_ratings": entity_ratings
            for entity, entity_ratings in entity_ratings.items()
        }
        logger.debug("rating_dict: %s", rating_dict)

        body = mbxml.make_rating_request(**rating_dict)  # type: ignore
        return body

    def submit_ratings(
        self,
        entity_ratings: Dict[str, Dict[MBId, Rating]],
    ):
        """
        Submit ratings to the API

        Parameters
        ----------
        entity_ratings
            The ratings to submit for each type of entity
        """
        # generate the dict to pass to mbxml
        if any(
            entity not in RATING_SUPPORTED_ENTITIES
            for entity in entity_ratings
        ):
            raise UnsupportedEntityError(
                entity_ratings.keys(),
                RATING_SUPPORTED_ENTITIES,
            )

        response = self._make_post_request(
            WSEndpoint.RATING.value,
            data=self._get_ratings_dict(entity_ratings),
        )
        return response
