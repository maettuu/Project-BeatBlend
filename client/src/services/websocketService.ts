import { Session } from "@/types/Session";
import { Playlist } from "@/types/Playlist";
import { SongList } from "@/types/Song";


class WebsocketService<Type> {
    socket: WebSocket | null
    reconnectTimeout: number;
    maxReconnectAttempts: number;
    reconnectAttempts: number;
    typeAddress: string;

    constructor(typeAddress: string) {
        this.reconnectTimeout = 2000;
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.socket = null;
        this.typeAddress = typeAddress;
    }

    connect(
        sessionId: string,
        handler: ((message: Type) => void)
    ) {
        this.socket = new WebSocket(`${import.meta.env.VITE_WS_BASE_URL}/${this.typeAddress}/${sessionId}`)

        this.socket.onopen = () => {
            console.log('Websocket connection established!')
            this.reconnectAttempts = 0;
        }

        this.socket.onmessage = (event) => {
            console.log('Message received:' + event.data);
            handler(JSON.parse(event.data));
        }

        this.socket.onclose = (event) => {
            console.log('Websocket disconnected!')
            if (event.code !== 1001) { // Do not attempt to reconnect if the connection was closed normally from serverside (code 1001)
                this.attemptReconnect(sessionId, handler);
            }
        }

        this.socket.onerror = (event) => {
            console.log('Websocket error:' + event)
            this.socket?.close()
        }
    }

    attemptReconnect(
        sessionId: string,
        handler: ((message: Type) => void)
    ) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                console.log('Attempting to reconnect to WebSocket...');
                this.reconnectAttempts++;
                this.connect(sessionId, handler);
            }, this.reconnectTimeout);
            this.reconnectTimeout *= 2; // Exponential backoff
        } else {
            console.log('Max reconnection attempts reached. Could not reconnect to WebSocket.');
        }
    }

    sendMessage(message: string) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket?.send(message);
        } else {
            console.log('WebSocket is not open. Cannot send message.');
        }
    }

    close() {
        this.socket?.close(1000, 'Client closed connection.'); // Close with normal closure code 1000
    }
}

export class SessionWebsocketService extends WebsocketService<Session> {
    constructor() {
        super("sessions");
    }
}

export class PlaylistWebsocketService extends WebsocketService<Playlist> {
    constructor() {
        super("playlist");
    }
}

export class RecommendationWebsocketService extends WebsocketService<SongList> {
    constructor() {
        super("recommendations");
    }
}
