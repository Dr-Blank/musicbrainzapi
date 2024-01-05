""" Models for the MusicBrainz API """

from dataclasses import dataclass
from typing import Optional

from .enums import CoreEntities


@dataclass
class MBEntity:
    """Base class for entities."""

    mbid: str
    """The MusicBrainz Identifier for the entity"""

    mb_type: CoreEntities
    """The type of the entity"""

    name: Optional[str] = None
    """The name of the entity"""

    rating: Optional[float] = None
    """The rating of the entity"""
