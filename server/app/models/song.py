from pydantic import model_validator
from datetime import datetime
from typing import Optional
from .user import User
from .camel_model import CamelModel

# scheiss idiotische approach zum arbiträr values setze aber you do you.
# mit de neue DB hemmer immerhin ermittleti wert womer üs sicher chönd si was max und was min isch
# Approximate values for maximum and minimum values of tempo.
MAX_TEMPO = 236
MIN_TEMPO = 0


class Song(CamelModel):
    id: Optional[str] = None
    track_name: Optional[str] = None
    album: Optional[str] = None
    album_id: Optional[str] = None
    artists: list[str] = []
    artist_ids: list[str] = []
    danceability: Optional[float] = None
    energy: Optional[float] = None
    speechiness: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    scaled_tempo: Optional[float] = None
    duration_ms: Optional[int] = None
    release_date: Optional[datetime] = None
    popularity: Optional[float] = None
    # below this: added manually (not in database)
    genre: list[str] = []
    preview_url: Optional[str] = None
    added_by: Optional[User] = None
    most_significant_feature: Optional[str] = None
    similarity_score: Optional[float] = -1.0
    is_first_recommendation: Optional[bool] = False
    votes: list[str] = []

    @model_validator(mode='after')
    def set_scaled_tempo(self) -> 'Song':
        # mit de ermittlete wert muesches au nüm so komplett hirngschisse clampe
        self.scaled_tempo = (self.tempo - MIN_TEMPO) / (MAX_TEMPO - MIN_TEMPO)
        # Clamp between 0 and 1
        # self.scaled_tempo = max(0, min(scaled_tempo, 1))
        return self


class SongList(CamelModel):
    songs: list[Song] = []
    voting_start_time: Optional[datetime] = None


class Playlist(CamelModel):
    played_songs: list[Song] = []
    current_song: Optional[Song] = None
    queued_songs: list[Song] = []

    def get_all_songs(self) -> list[Song]:
        songs = self.played_songs.copy()
        if self.current_song:
            songs.append(self.current_song)
        songs.extend(self.queued_songs)
        return songs
