from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from .albums import Album, Artists
from datetime import date


class ContentRating(BaseModel):
    label: str


class Duration(BaseModel):
    totalMilliseconds: int


class Playability(BaseModel):
    playable: bool


class Track(BaseModel):
    uri: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    albumOfTrack: Optional[Album] = None
    artists: Optional[Artists] = None
    contentRating: Optional[ContentRating] = None
    duration: Optional[Duration] = None
    playability: Optional[Playability] = None


class TrackItem(BaseModel):
    data: Optional[Track] = None  # Sometimes data can be empty list or null


class PagingInfo(BaseModel):
    nextOffset: int
    limit: int


class TrackList(BaseModel):
    totalCount: Optional[int] = None
    items: Optional[List[TrackItem]] = None
    pagingInfo: Optional[PagingInfo] = None


class TracksResponse(BaseModel):
    tracks: Optional[TrackList] = None


class TrackSearch(BaseModel):
    query: str
    limit: Optional[int] = 20
    offset: Optional[int] = 0


class Period(str, Enum):
    daily = "daily"
    weekly = "weekly"


class Country(str, Enum):
    GLOBAL = "GLOBAL"
    AR = "AR"
    AU = "AU"
    AT = "AT"
    BY = "BY"
    BE = "BE"
    BO = "BO"
    BR = "BR"
    BG = "BG"
    CA = "CA"
    CL = "CL"
    CO = "CO"
    CR = "CR"
    CY = "CY"
    CZ = "CZ"
    DK = "DK"
    DO = "DO"
    EC = "EC"
    EE = "EE"
    EG = "EG"
    SV = "SV"
    FI = "FI"
    FR = "FR"
    DE = "DE"
    GR = "GR"
    GT = "GT"
    HN = "HN"
    HK = "HK"
    HU = "HU"
    IS = "IS"
    IN = "IN"
    ID = "ID"
    IE = "IE"
    IL = "IL"
    JP = "JP"
    KZ = "KZ"
    LV = "LV"
    LT = "LT"
    LU = "LU"
    MY = "MY"
    MX = "MX"
    MA = "MA"
    NL = "NL"
    NZ = "NZ"
    NI = "NI"
    NG = "NG"
    NO = "NO"
    PK = "PK"
    PA = "PA"
    PY = "PY"
    PE = "PE"
    PH = "PH"
    PL = "PL"
    PT = "PT"
    RO = "RO"
    SA = "SA"
    SG = "SG"
    SK = "SK"
    ZA = "ZA"
    KR = "KR"
    ES = "ES"
    SE = "SE"
    CH = "CH"
    TW = "TW"
    TH = "TH"
    TR = "TR"
    AE = "AE"
    UA = "UA"
    GB = "GB"
    UY = "UY"
    US = "US"
    VE = "VE"
    VN = "VN"


class TopTrendingTracks(BaseModel):
    country: Optional[Country] = Country.VN
    period: Optional[Period] = Period.daily


# Models for top_trending_tracks_handler response
class TrendingTrackArtist(BaseModel):
    name: str
    spotifyUri: str
    externalUrl: Optional[str] = ""


class TrendingTrackLabel(BaseModel):
    name: str
    spotifyUri: Optional[str] = ""
    externalUrl: Optional[str] = ""


class RankingMetric(BaseModel):
    value: str
    type: str


class ChartEntryData(BaseModel):
    currentRank: int
    previousRank: int
    peakRank: int
    peakDate: str
    appearancesOnChart: int
    consecutiveAppearancesOnChart: int
    rankingMetric: RankingMetric
    entryStatus: str
    entryRank: int
    entryDate: str


class TrendingTrackMetadata(BaseModel):
    trackName: str
    trackUri: str
    displayImageUri: str
    artists: List[TrendingTrackArtist]
    producers: List[Any] = []
    labels: List[TrendingTrackLabel] = []
    songWriters: List[Any] = []
    releaseDate: str


class TrendingTrack(BaseModel):
    chartEntryData: ChartEntryData
    missingRequiredFields: bool
    trackMetadata: TrendingTrackMetadata


class TrendingTracksResponse(BaseModel):
    tracks: List[TrendingTrack]
