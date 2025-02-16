import { Song } from '@/types/Song';

export class Playlist {
    playedSongs: Song[]
    currentSong: Song | null
    queuedSongs: Song[]

    constructor(data: Playlist) {
        this.playedSongs = data.playedSongs
        this.currentSong = data.currentSong
        this.queuedSongs = data.queuedSongs
    }
}

export function flattenPlaylist(playlist: Playlist) {
    return playlist.playedSongs.concat(playlist.currentSong ? [playlist.currentSong] : []).concat(playlist.queuedSongs.map((song) => {
        return {
            ...song,
            isQueued: true,
        };
    }));
}
