from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from .albums import Album, Artists
from datetime import date, datetime


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

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class PagingInfo(BaseModel):
    nextOffset: int
    limit: int


class TrackList(BaseModel):
    totalCount: Optional[int] = None
    items: Optional[List[TrackItem]] = None
    pagingInfo: Optional[PagingInfo] = None

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


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
    USUK = "USUK"
    KR = "KR"
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

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class DownloadTrackData(BaseModel):
    id: Optional[str] = None
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    cover: Optional[str] = None
    releaseDate: Optional[str] = None
    downloadLink: Optional[str] = None


class DownloadTrackResponse(BaseModel):
    success: Optional[bool] = None
    data: Optional[DownloadTrackData] = None
    generatedTimeStamp: Optional[int] = None

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class LyricSyllable(BaseModel):
    pass  # Currently empty based on sample response


class LyricLine(BaseModel):
    startTimeMs: str
    words: str
    syllables: List[LyricSyllable] = []
    endTimeMs: str


class LyricsProvider(BaseModel):
    syncType: str
    lines: List[LyricLine]
    provider: str
    providerLyricsId: str
    providerDisplayName: str
    syncLyricsUri: str
    isDenseTypeface: bool
    alternatives: List[Any] = []
    language: str
    isRtlLanguage: bool
    capStatus: str
    previewLines: List[LyricLine]


class LyricsColors(BaseModel):
    background: int
    text: int
    highlightText: int


class TrackLyricsResponse(BaseModel):
    lyrics: LyricsProvider
    colors: LyricsColors
    hasVocalRemoval: bool

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class PopularSong(BaseModel):
    title: str
    artist: str
    genre: str
    year: str

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class PopularSongsResponse(BaseModel):
    data: List[PopularSong]

    def model_dump(self) -> Dict[str, Any]:
        return self.dict(exclude_none=True)


class MusicTrack(BaseModel):
    """Music track model with all fields required for the frontend."""

    id: str
    name: str
    artist: List[str]
    albumArt: str
    audioUrl: str  # URL or asset path for the audio file
    lyrics: TrackLyricsResponse
    duration: int  # Duration in milliseconds
    listener: int
    releaseDate: Optional[str] = None
    nation: Optional[str] = None

    class Config:
        orm_mode = True  # This allows the model to work with ORM objects


class MusicTrackListResponse(BaseModel):
    """Response model containing a list of music tracks."""

    success: bool = True
    data: list[MusicTrack]
    total: int
    message: Optional[str] = None
