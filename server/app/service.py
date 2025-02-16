import jwt
import os
import asyncio
import uuid
import math
import requests

from datetime import timedelta, datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from typing import Annotated
from asyncio import Task
from collections import defaultdict

from models.user import User, SpotifyUser
from models.token import Token, SpotifyToken
from models.session import SessionCore, Session
from models.song import Song, SongList, Playlist
from models.artifact import Artifact, AverageFeatures
from repository import Repository
from ws.websocket_manager import WebsocketManager

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 720))
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
DISCOGS_API_URL = os.getenv("DISCOGS_API_URL")
DISCOGS_API_TOKEN = os.getenv("DISCOGS_API_TOKEN")
BASE_URL = os.getenv("BASE_URL")


class Service:
    def __init__(self, repository: Repository, websocket_manager: WebsocketManager):
        self.repo = repository
        self.manager = websocket_manager
        self.spotify_oauth = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope="user-library-read"  # scope defines functionalities
        )
        self.spotify_api_client = Spotify(auth_manager=self.spotify_oauth)
        self.session_lock = asyncio.Lock()
        self.asyncio_tasks = defaultdict(list)

    @staticmethod
    def with_session_lock(func):
        async def wrapper(self, *args):
            async with self.session_lock:
                return await func(self, *args)

        return wrapper

    def get_spotify_token(self, host: SpotifyUser) -> SpotifyToken:
        try:
            spotify_token_info = self.spotify_oauth.get_access_token(host.auth_code, check_cache=False)
            return SpotifyToken(**spotify_token_info)
        except SpotifyOauthError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization code")

    @staticmethod
    def get_display_name(token: SpotifyToken) -> str:
        try:
            spotify_host_client = Spotify(auth=token.access_token)
            user_info = spotify_host_client.current_user()
            return user_info['display_name']
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request unsuccessful: {repr(e)}")

    async def create_user(self, user: User) -> User:
        user.id = str(uuid.uuid4())
        await self.repo.set_user(user)
        return user

    @staticmethod
    def generate_token(user: User, spotify_token: SpotifyToken = None) -> Token:
        to_encode = {"sub": user.id, "username": user.username}
        if spotify_token:  # additionally encode the spotify token for hosts
            to_encode["spotify_token"] = spotify_token.model_dump()
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return Token(access_token=encoded_jwt, token_type="bearer")

    @staticmethod
    def verify_token(token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="token"))]) -> str:
        auth_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized!")
        try:
            payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                raise auth_exception
        except InvalidTokenError:
            raise auth_exception
        # TODO: Consider also returing the spotify token.
        return user_id

    async def verify_user(self, user_id: str) -> None:
        await self.repo.verify_user_by_id(user_id)

    async def verify_session(self, session_id: str) -> None:
        await self.repo.verify_session_by_id(session_id)

    async def verify_instances(self, user_ids: str | list[str] = "", session_id: str = ""):
        if isinstance(user_ids, str) and user_ids:
            await self.verify_user(user_ids)
        elif isinstance(user_ids, list):
            for user_id in user_ids:
                await self.verify_user(user_id)
        if session_id:
            await self.verify_session(session_id)

    async def get_user(self, user_id: str) -> User:
        result = await self.repo.get_user_by_id(user_id)
        return User.model_validate_json(result)

    # @staticmethod
    # async def get_genre(song: Song) -> None:
    #     params = {
    #         'release_title': song.album,
    #         'artist': ', '.join(song.artists),
    #         'type': 'release',  # album/single/EP
    #         'token': DISCOGS_API_TOKEN
    #     }
    #
    #     response = requests.get(DISCOGS_API_URL, params=params)
    #     if response.status_code == 200:
    #         data = response.json()
    #         if 'results' in data and len(data['results']) > 0:
    #             result = data['results'][0]  # first result is most relevant
    #             genres = result.get('genre', [])
    #             song.genre = genres
    #     else:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Discogs could not be reached")

    # async def get_popularity_and_preview_url(self, song: Song) -> None:
    #     try:
    #         song_info = self.spotify_api_client.track(song.id)
    #         song.preview_url = song_info.get('preview_url')
    #         song.popularity = song_info.get('popularity')
    #     except Exception as e:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request unsuccessful: {repr(e)}")

    async def get_session(self, session_id: str) -> Session:
        result = await self.repo.get_session_by_id(session_id)
        return Session.model_validate_json(result)

    @with_session_lock
    async def set_most_popular_recommendation(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        if not session.playlist.queued_songs:
            session.playlist.queued_songs.append(max(session.recommendations, key=lambda recommendation: len(recommendation.votes)))
            await self.repo.set_session(session)

    async def generate_recommendations(self, session: Session, limit: int) -> list[Song]:
        result = await self.repo.get_recommendations_by_songs(session.id, session.playlist.get_all_songs(), limit)
        recommendations = []
        first_recommendation = True
        for row in result:
            song = await self.get_song_from_database(row['id'])
            # await self.get_genre(song)
            # await self.get_popularity_and_preview_url(song)
            diffs = {
                'danceability': row['diff_danceability'],
                'energy': row['diff_energy'],
                'speechiness': row['diff_speechiness'],
                'valence': row['diff_valence'],
                'tempo': row['diff_tempo']
            }
            song.most_significant_feature = max(diffs, key=diffs.get)
            song.similarity_score = (1 - (row['cosine_distance'] / math.sqrt(5)))
            if first_recommendation:
                song.is_first_recommendation = True
                first_recommendation = False
            recommendations.append(song)
        return recommendations

    @with_session_lock
    async def set_session_recommendations(self, session_id: str, recommendations: list[Song]) -> Session:
        session = await self.get_session(session_id)
        session.recommendations.clear()
        session.recommendations.extend(recommendations)
        await self.repo.set_session(session)
        return session

    async def generate_session_recommendations(self, session_id: str, limit: int = 3, automation_task: bool = False) -> None:
        session = await self.get_session(session_id)
        start_generation_duration = datetime.now()
        recommendations = await self.generate_recommendations(session, limit)
        generation_duration = (datetime.now() - start_generation_duration).total_seconds()
        if generation_duration < 3:
            await asyncio.sleep(3)
        session = await self.set_session_recommendations(session.id, recommendations)
        if not automation_task:  # generation was not invoked by automation, remove current asyncio task here
            await self.manager.publish(
                channel=f"recommendations:{session.id}",
                message=SongList(
                    songs=session.recommendations
                )
            )
            self.asyncio_tasks[session.id].remove(asyncio.current_task())

    @with_session_lock
    async def update_current_song_and_queue(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        session.voting_start_time = None
        if session.playlist.current_song:
            session.playlist.played_songs.append(session.playlist.current_song)
            session.playlist.current_song = None
        session.playlist.current_song = session.playlist.queued_songs.pop(0)
        await self.repo.set_session(session)
        await self.manager.publish(channel=f"playlist:{session.id}", message=session.playlist)

    @with_session_lock
    async def start_voting(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        session.voting_start_time = datetime.now().timestamp()
        await self.repo.set_session(session)
        await self.manager.publish(
            channel=f"recommendations:{session.id}",
            message=SongList(
                songs=session.recommendations,
                voting_start_time=session.voting_start_time
            )
        )

    async def check_for_empty_queue(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        if not session.playlist.queued_songs:
            await self.generate_session_recommendations(session.id, automation_task=True)
            await self.start_voting(session.id)
        self.asyncio_tasks[session.id].remove(asyncio.current_task())

    async def advance_playlist(self, session_id: str) -> Task:
        await self.set_most_popular_recommendation(session_id)
        await self.update_current_song_and_queue(session_id)
        generation_task = asyncio.create_task(self.check_for_empty_queue(session_id))
        self.asyncio_tasks[session_id].append(generation_task)
        return generation_task

    async def automate(self, session_id: str, generation_task: Task = None):
        await asyncio.sleep(30)
        if generation_task:  # failsafe in case generation hasn't finished after 30 seconds
            await generation_task
        generation_task = await self.advance_playlist(session_id)
        await self.automate(session_id, generation_task)

    async def create_session(self, host_id: str, session: Session) -> Session:
        host = await self.get_user(host_id)
        session.id = str(uuid.uuid4())
        session.host_id = str(host.id)
        session.host_name = host.username
        session.creation_date = datetime.now()
        session.invite_link = f'{BASE_URL}/{session.id}/join'
        for song in session.playlist.queued_songs:
            song.added_by = host
            # await self.get_genre(song)
            # await self.get_popularity_and_preview_url(song)
        await self.repo.set_session(session)
        await self.advance_playlist(session.id)
        self.asyncio_tasks[session.id].append(asyncio.create_task(self.generate_session_recommendations(session.id)))
        self.asyncio_tasks[session.id].append(asyncio.create_task(self.automate(session.id)))
        return await self.get_session(session.id)

    @staticmethod
    def verify_host_of_session(host_id: str, session: Session) -> None:
        if session.host_id != host_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not host of session.")

    async def create_artifact(self, session: Session) -> Artifact:
        played_songs = session.playlist.played_songs

        total_manually_added_songs = 0
        total_songs_added_per_user = defaultdict(int)
        total_votes_per_user = defaultdict(int)
        total_per_significant_feature = defaultdict(int)
        first_recommendation_wins = 0
        total_recommended_songs = False

        total_danceability = 0.0
        total_energy = 0.0
        total_speechiness = 0.0
        total_valence = 0.0
        total_scaled_tempo = 0.0

        for song in played_songs:
            if song.added_by:
                total_manually_added_songs += 1
                total_songs_added_per_user[song.added_by.id] += 1
            else:
                total_recommended_songs += 1
                if song.is_first_recommendation and song.votes:  # TODO: "and song.votes" can be removed if we simply want to count number of top recommendations
                    first_recommendation_wins += 1

                total_per_significant_feature[song.most_significant_feature] += 1

            total_danceability += song.danceability or 0.0
            total_energy += song.energy or 0.0
            total_speechiness += song.speechiness or 0.0
            total_valence += song.valence or 0.0
            total_scaled_tempo += song.scaled_tempo or 0.0

            if song.votes:
                for voter_id in song.votes:
                    total_votes_per_user[voter_id] += 1

        total_songs = len(played_songs)
        average_features = AverageFeatures(
            danceability=total_danceability / total_songs if total_songs else 0.0,
            energy=total_energy / total_songs if total_songs else 0.0,
            speechiness=total_speechiness / total_songs if total_songs else 0.0,
            valence=total_valence / total_songs if total_songs else 0.0,
            scaled_tempo=total_scaled_tempo / total_songs if total_songs else 0.0
        )

        most_songs_added = max(total_songs_added_per_user.values(), default=-1)
        user_id_most_songs_added = [user_id for user_id, count in total_songs_added_per_user.items() if count == most_songs_added]  # checks for multiple max counts
        most_songs_added_by = [await self.get_user(user_id) for user_id in user_id_most_songs_added]
        most_votes = max(total_votes_per_user.values(), default=-1)
        user_id_most_votes = [user_id for user_id, count in total_votes_per_user.items() if count == most_votes]  # check for multiple max counts
        most_votes_by = [await self.get_user(user_id) for user_id in user_id_most_votes]
        most_significant_feature_overall = max(total_per_significant_feature, key=total_per_significant_feature.get, default=None)

        first_recommendation_vote_percentage = (
            (first_recommendation_wins / total_recommended_songs) * 100 if total_recommended_songs else 0.0
        )

        return Artifact(
            songs_played=total_songs,
            songs_added_manually=total_manually_added_songs,
            most_songs_added_by=[user.username for user in most_songs_added_by] if most_songs_added_by else None,
            most_votes_by=[user.username for user in most_votes_by] if most_votes_by else None,
            most_significant_feature_overall=most_significant_feature_overall,
            first_recommendation_vote_percentage=round(first_recommendation_vote_percentage, 1),
            average_features=average_features,
            genre_start=played_songs[0].genre if played_songs else None,
            genre_end=played_songs[-1].genre if played_songs else None
        )

    @with_session_lock
    async def end_session(self, host_id: str, session_id: str):
        session = await self.get_session(session_id)
        self.verify_host_of_session(host_id, session)
        automation_task = self.asyncio_tasks.get(session.id)
        if automation_task:
            for task in automation_task:
                task.cancel()
        del self.asyncio_tasks[session.id]
        session_artifact = await self.create_artifact(session)
        await self.repo.delete_session_by_id(session.id)
        return session_artifact

    @with_session_lock
    async def add_guest_to_session(self, guest_id: str, session_id: str) -> Session:
        guest = await self.get_user(guest_id)
        session = await self.get_session(session_id)

        if guest_id not in session.guests:
            session.guests[guest_id] = guest
            await self.repo.set_session(session)
            await self.manager.publish(channel=f"session:{session_id}", message=SessionCore(**session.model_dump()))
        return session

    @staticmethod
    def verify_guest_of_session(guest_id: str, session: Session) -> None:
        if guest_id not in session.guests:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guest not part of session.")

    @with_session_lock
    async def remove_guest_from_session(self, host_id: str, guest_id: str, session_id: str) -> None:
        session = await self.get_session(session_id)
        if host_id:
            self.verify_host_of_session(host_id, session)
        self.verify_guest_of_session(guest_id, session)
        del session.guests[guest_id]
        await self.repo.set_session(session)
        await self.manager.publish(channel=f"session:{session_id}", message=SessionCore(**session.model_dump()))

    async def get_song_from_database(self, song_id: str) -> Song:
        result = await self.repo.get_song_by_id(song_id)
        song = Song.model_validate(dict(result))
        # await self.get_genre(song)
        # await self.get_popularity_and_preview_url(song)
        return song

    # async def add_song_to_database(self, song_id: str) -> Song:
    #     try:
    #         song_info = self.spotify_api_client.track(song_id)
    #         audio_features = self.spotify_api_client.audio_features(song_id)[0]
    #         combined_info = {**song_info, **audio_features}
    #
    #         album_info = combined_info.get('album', {})
    #         artists_info = combined_info.get('artists', [])
    #         release_date_str = album_info.get('release_date')
    #         release_date = None
    #         if release_date_str:
    #             try:
    #                 release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
    #             except ValueError:
    #                 release_date = None
    #
    #         filtered_song_info = {
    #             "id": str(combined_info.get('id', '')),
    #             "track_name": str(combined_info.get('name', '')),
    #             "album": str(album_info.get('name', '')),
    #             "album_id": str(album_info.get('id', '')),
    #             "artists": [str(artist['name']) for artist in artists_info],
    #             "artist_ids": [str(artist['id']) for artist in artists_info],
    #             "danceability": float(combined_info.get('danceability', 0.0)),
    #             "energy": float(combined_info.get('energy', 0.0)),
    #             "speechiness": float(combined_info.get('speechiness', 0.0)),
    #             "valence": float(combined_info.get('valence', 0.0)),
    #             "tempo": float(combined_info.get('tempo', 0.0)),
    #             "duration_ms": int(combined_info.get('duration_ms', 0)),
    #             "release_date": release_date,
    #             "popularity": float(combined_info.get('popularity', 0.0))
    #         }
    #
    #         await self.repo.add_song_by_info(filtered_song_info)
    #         filtered_song_info["preview_url"] = combined_info.get('preview_url')
    #         song = Song(**filtered_song_info)
    #         # await self.get_genre(song)
    #         return song
    #     except Exception as e:
    #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request unsuccessful: {repr(e)}")

    # async def delete_song_from_database(self, song_id: str) -> None:
    #     await self.repo.delete_song_by_id(song_id)

    async def get_song(self, song_id: str) -> Song:
        try:
            return await self.get_song_from_database(song_id)
        except HTTPException:
            # return await self.add_song_to_database(song_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    @with_session_lock
    async def add_song_to_session(self, user_id: str, session_id: str, song_id: str) -> Playlist:
        user = await self.get_user(user_id)
        session = await self.get_session(session_id)
        if user.id not in session.guests and user.id != session.host_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not part of session")
        song = await self.get_song(song_id)
        song.added_by = user
        session.playlist.queued_songs.append(song)
        await self.repo.set_session(session)
        await self.manager.publish(channel=f"playlist:{session.id}", message=session.playlist)
        self.asyncio_tasks[session.id].append(asyncio.create_task(self.generate_session_recommendations(session.id)))
        return session.playlist

    @with_session_lock
    async def remove_song_from_session(self, host_id: str, session_id: str, song_id: str) -> None:
        session = await self.get_session(session_id)
        self.verify_host_of_session(host_id, session)
        for idx, song in enumerate(session.playlist.queued_songs):
            if song.id == song_id:
                del session.playlist.queued_songs[idx]
                await self.repo.set_session(session)
                await self.manager.publish(channel=f"playlist:{session.id}", message=session.playlist)
                self.asyncio_tasks[session.id].append(asyncio.create_task(self.generate_session_recommendations(session.id)))
                return

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not part of playlist")

    async def get_session_recommendations(self, session_id: str) -> SongList:
        session = await self.get_session(session_id)
        return SongList(songs=session.recommendations)

    @with_session_lock
    async def add_or_change_vote_to_recommendation(self, guest_id: str, session_id: str, song_id: str) -> SongList:
        session = await self.get_session(session_id)
        self.verify_guest_of_session(guest_id, session)
        curr_rec = next((rec for rec in session.recommendations if rec.id == song_id), None)
        if not curr_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song is not recommended.")
        previous_rec = next((rec for rec in session.recommendations if guest_id in rec.votes), None)  # not None if guest has previously voted
        if previous_rec:
            previous_rec.votes.remove(guest_id)
        if guest_id in curr_rec.votes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vote already added.")
        curr_rec.votes.append(guest_id)
        await self.repo.set_session(session)
        response = SongList(songs=session.recommendations)
        await self.manager.publish(channel=f"recommendations:{session_id}", message=response)
        return response

    @with_session_lock
    async def remove_vote_from_recommendation(self, guest_id: str, session_id: str, song_id: str) -> None:
        session = await self.get_session(session_id)
        self.verify_guest_of_session(guest_id, session)
        curr_rec = next((rec for rec in session.recommendations if rec.id == song_id), None)
        if not curr_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song is not recommended.")
        if guest_id not in curr_rec.votes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No vote added prior.")
        curr_rec.votes.remove(guest_id)
        await self.repo.set_session(session)
        await self.manager.publish(channel=f"recommendations:{session_id}", message=SongList(songs=session.recommendations))

    async def get_matching_songs_from_database(self, pattern: str, limit: int) -> SongList:
        result = await self.repo.get_songs_by_pattern(pattern, limit)
        songs = [Song.model_validate(dict(row)) for row in result]
        return SongList(songs=songs)
