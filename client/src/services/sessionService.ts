import apiClient from '@/services/axios';
import { Session } from '@/types/Session';
import { Song } from '@/types/Song';
import { SongFeatureCategory } from '@/types/SongFeature';
import type { SongFeature } from '@/types/SongFeature';
import { Artifacts } from '@/types/Artifact';
import { SongList } from '@/types/Song';

export const sessionService = {

    async joinSession(sessionId: string): Promise<Session> {
        return apiClient.patch(`/sessions/${sessionId}/guests`).then((response) => {
            return response.data;
        })
    },
    async removeGuest(sessionId: string, guestId: string): Promise<void> {
        await apiClient.delete(`/sessions/${sessionId}/guests/${guestId}`);
    },
    async getSessions(): Promise<Session[]> {
        return apiClient.get('/sessions').then((response) => {
            return response.data;
        })
    },
    async endSession(sessionId: string): Promise<Artifacts> {
        return apiClient.delete(`/sessions/${sessionId}`).then((response) => {
            return response.data;
        });
    },
    async getSessionById(sessionId: string): Promise<Session> {
        return apiClient.get(`/sessions/${sessionId}`).then((response) => {
            response.data.isRunning = true;
            return response.data;
        })
    },
    async getSongs(pattern: string): Promise<Song[]> {
        return apiClient.get(`/songs`, {params: {pattern}}).then((response) => {
            return response.data['songs'];
        })
    },
    async createNewSession(session: Session): Promise<Session> {
        return apiClient.post(`/sessions`, {...session}).then((response) => {
            response.data.isRunning = true;
            return response.data;
        })
    },
    async getRecommendations(sessionId: string): Promise<SongList> {
        return apiClient.get(`/sessions/${sessionId}/recommendations`).then((response) => {
            return response.data;
        })
    },
    async addSong(sessionId: string, songId: string): Promise<Session> {
        return apiClient.patch(
            `/sessions/${sessionId}/songs`, null,
            {params: {"song_id": songId}}).then((response) => {
            return response.data;
        })
    },
    async addVote(sessionId: string, songId: string): Promise<void> {
        return apiClient.patch(`/sessions/${sessionId}/recommendations/${songId}/vote`);
    },
    async deleteVote(sessionId: string, songId: string): Promise<void> {
        return apiClient.delete(`/sessions/${sessionId}/recommendations/${songId}/vote`);
    },
};

export const getSongFeatures = (song: Song): SongFeature[] => {
    return [
        {
            category: SongFeatureCategory.TEMPO,
            value: song.scaledTempo
        },
        {
            category: SongFeatureCategory.ENERGY,
            value: song.energy
        },
        {
            category: SongFeatureCategory.VALENCE,
            value: song.valence
        },
            {
            category: SongFeatureCategory.DANCEABILITY,
            value: song.danceability
        },
        {
            category: SongFeatureCategory.SPEECHINESS,
            value: song.speechiness
        },
    ];
}

export const getSongFeatureCategory = (feature: string) => {
    switch (feature) {
        case "tempo":
            return SongFeatureCategory.TEMPO;
        case "danceability":
            return SongFeatureCategory.DANCEABILITY;
        case "energy":
            return SongFeatureCategory.ENERGY;
        case "speechiness":
            return SongFeatureCategory.SPEECHINESS;
        case "valence":
            return SongFeatureCategory.VALENCE;
        default:
            return null;
    }
}