import {defineStore} from 'pinia'
import {ref} from 'vue'
import {sessionService} from '@/services/sessionService'
import {Session} from '@/types/Session'
import {Playlist} from '@/types/Playlist'
import { SongList } from '@/types/Song'
import { Artifacts } from '@/types/Artifact'
import { SessionWebsocketService, PlaylistWebsocketService, RecommendationWebsocketService } from "@/services/websocketService";

export const useSession = defineStore('session', () => {

    const session = ref<Session | null>(null);

    const sessionSocket = new SessionWebsocketService();
    const playlistSocket = new PlaylistWebsocketService();
    const recommendationsSocket = new RecommendationWebsocketService();

    const storedSessionId = localStorage.getItem('sessionId')

    const handleSessionMessages = (sessionMessage: Session) => {
        const playlist = sessionMessage.playlist || session.value.playlist;
        const recommendations = sessionMessage.recommendations || session.value.recommendations;
        const votingStartTime = sessionMessage.recommendations || session.value.votingStartTime;
        session.value = {
            isRunning: session.value.isRunning,
            ...sessionMessage,
            playlist,
            recommendations,
            votingStartTime,
        };
    };
      
    const handlePlaylistMessages = (playlistMessage: Playlist) => {
        session.value.recommendations = [];
        session.value.playlist = playlistMessage;
    };
      
    const handleRecommendationMessages = (recommendationMessage: SongList) => {
       session.value.recommendations = recommendationMessage.songs;
       if (recommendationMessage.votingStartTime) {
         session.value.votingStartTime = recommendationMessage.votingStartTime;
       }
    };

    const fetchRecommendations = async () => {
        console.log("Fetching recommendations");
        handleRecommendationMessages(await sessionService.getRecommendations(session.value.id));
    }

    const initialize = async () => {
        session.value.isRunning = true;
        await fetchRecommendations();

        localStorage.setItem('sessionId', session.value.id);

        sessionSocket.connect(session.value.id, handleSessionMessages);
        playlistSocket.connect(session.value.id, handlePlaylistMessages);
        recommendationsSocket.connect(session.value.id, handleRecommendationMessages);
    }

    const fetchSession = async (sessionId: string | null) => {
        const id = sessionId || storedSessionId;
        if (!id) {
            return;
        }
        try {
            session.value = await sessionService.getSessionById(id);
            session.value.artifacts = session.value.artifacts || null;
            return initialize();
        } catch (error) {
            localStorage.removeItem('sessionId');
        }
    }

    const createSession = async (newSession: Session) => {
        session.value = await sessionService.createNewSession(newSession);
        return initialize();
    }

    const endSession = async () => {
        if (!session.value) return;

        try {
            const artifactData = await sessionService.endSession(session.value.id);

            if (artifactData) {
                session.value.artifacts = new Artifacts(artifactData);
            }

            session.value.isRunning = false;
            session.value.guests = {};

            sessionSocket.close();
            playlistSocket.close();
            recommendationsSocket.close();
        } catch (error) {
            console.error ("Failed to end session or fetch artifacts", error);
        }
    };
    return {session, fetchSession, createSession, endSession};
});


