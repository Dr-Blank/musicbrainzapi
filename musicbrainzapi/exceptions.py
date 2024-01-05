"""Exceptions for the API."""

from typing import Iterable, Union

import requests

from .enums import CoreEntities


class UnsupportedEntityError(ValueError):
    """Raised when an entity is not supported."""

    def __init__(
        self,
        entity: Union[str, Iterable[str]],
        supported_entities: Iterable[CoreEntities],
    ) -> None:
        self.supported_entities = supported_entities

        if not isinstance(entity, str):
            entity = set(entity) - set(supported_entities)

        self.entity = entity
        super().__init__(
            "Only the following entities are supported:"
            f" {supported_entities}\nReceived: {entity}"
        )


class APIError(requests.exceptions.RequestException):
    """Base class for API errors."""

    def __init__(self, response: requests.Response) -> None:
        self.response = response
        self.status_code = response.status_code
        self.reason = response.reason
        self.url = response.url
        self.text = response.text
        self.headers = response.headers

        super().__init__(f"{self.status_code} {self.reason} for {self.url}")


class NotFoundError(APIError):
    """Raised when a resource is not found."""


class ServerError(APIError):
    """Raised when the server returns an error."""


class RateLimitError(APIError):
    """Raised when the rate limit is exceeded."""
