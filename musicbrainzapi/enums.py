"""Enums for the musicbrainz api"""

from enum import Enum

__all__ = [
    "CoreEntities",
    "NonCoreResources",
    "UniqueIdentifiers",
    "RATING_SUPPORTED_ENTITIES",
]


class CoreEntities(str, Enum):
    """Core entities for the API"""

    AREA = "area"
    ARTIST = "artist"
    EVENT = "event"
    GENRE = "genre"
    INSTRUMENT = "instrument"
    LABEL = "label"
    PLACE = "place"
    RECORDING = "recording"
    RELEASE = "release"
    RELEASE_GROUP = "release-group"
    SERIES = "series"
    WORK = "work"
    URL = "url"


class NonCoreResources(str, Enum):
    """Non core resources for the API"""

    RATING = "rating"
    TAG = "tag"
    COLLECTION = "collection"


class UniqueIdentifiers(str, Enum):
    """Unique identifiers for the API"""

    DISCID = "discid"
    ISRC = "isrc"
    ISWC = "iswc"


RATING_SUPPORTED_ENTITIES = [
    CoreEntities.ARTIST,
    CoreEntities.LABEL,
    CoreEntities.RECORDING,
    CoreEntities.RELEASE_GROUP,
    CoreEntities.WORK,
]
