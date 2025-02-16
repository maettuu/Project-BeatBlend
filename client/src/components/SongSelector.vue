<template>
    <div class="songs">
        <h2 class="songs-header">{{ headerText }}</h2>
        <AutoComplete
            class="search" v-model="selectedSong"
            @option-select="selectSong"
            :suggestions="filteredSongs"
            @complete="search"
            variant="filled"
            :unstyled="false"
            overlayClass="overlay"
            placeholder="Search">
            <template #option="slotProps">
                <div class="song">
                    <i class="pi pi-play"></i>
                    <div class="song-details">
                        <span class="song-title">{{ slotProps.option.trackName }}</span>
                        <span class="song-artists">{{ combineArtists(slotProps.option.artists) }}</span>
                    </div>
                </div>
            </template>
            <template #empty>
                <div class="no-results">
                    No results found
                </div>
            </template>
        </AutoComplete>
        <div class="selected-songs">
            <div class="selected-song" v-for="song in selectedSongs" :key="song.id">
                <SongItem :song="song">
                    <i class="pi pi-trash delete-icon" @click="removeSong(song)"></i>
                </SongItem>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import AutoComplete from 'primevue/autocomplete';
import SongItem from '@/components/SongItem.vue';
import { sessionService } from '@/services/sessionService';

const props = defineProps({
    headerText: {
        type: String,
        required: true,
    },
});


const filteredSongs = ref([]);
const selectedSong = ref(null);
const selectedSongs = defineModel();

// Combines the artists into a single string.
const combineArtists = (artists: string[]) => {
    return artists.join(', ');
};

// Function which is executed by the autocomplete component,
// which filters the songs, based on the user query.
const search = async (event) => {
    if (!event.query.trim().length) {
        filteredSongs.value = [];
        return;
    } else {
        try {
            const songs = await sessionService.getSongs(event.query.toLowerCase());
            const selectedSongsIds = selectedSongs.value.map((song: Song) => song.id);
          filteredSongs.value = songs.filter((song: Song) => !selectedSongsIds.includes(song.id));
        } catch (error) {
            filteredSongs.value = [];
        }
    }
};

// Selects a song from the autocomplete options and adds it to the
// selected song list.
const selectSong = () => {
    selectedSongs.value = [...selectedSongs.value, selectedSong.value];
    selectedSong.value = null;
}

// Removes a song from the selected list.
const removeSong = (songToRemove: Song) => {
    selectedSongs.value = selectedSongs.value.filter((song: Song) => song.id !== songToRemove.id);
};

</script>

<style scoped>
.songs {
  background-color: var(--backcore-color1);
  height: 100%;
  margin: 10px var(--margin-inline) 80px;
  padding-inline: var(--margin-inline);
  border-radius: 15px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.songs-header {
  color: var(--font-color);
}

.search.p-autocomplete {
  display: block;
  background-color: var(--backcore-color2);
  border-radius: 15px;
  font-size: 16px;
  border: solid;
  border-color: var(--backcore-color3);
  border-width: 2px;
  padding: 5px 10px;
  box-sizing: border-box;
}

.songs input {
  background-color: var(--backcore-color3);
  font-family: inherit;
  color: var(--font-color);
}

input:focus {
    outline: none;
}

.songs .search.p-autocomplete ::placeholder {
    color: var(--backcore-color3);
}

.p-autocomplete-overlay.overlay {
    margin-top: 10px;
    background-color: var(--backcore-color3);
    color: var(--font-color);
    font-family: inherit;
    border-radius: 10px;
    overflow-y: auto;
    padding: 5px;
    width: 30%;
}

.search .p-autocomplete-loader {
  color: var(--font-color);
}

.p-autocomplete-overlay.overlay .song {
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-items: center;
    gap: 8px;
    color: var(--font-color);
    border-radius: 5px;
    padding: 5px;
    margin-inline: 5px;
    width: 100%;
}

.p-autocomplete-overlay.overlay .song-details, .song-details {
    display: flex;
    flex-direction: column;
    justify-content: start;
    gap: 2px;
}

.overlay .p-autocomplete-list {
    gap: 7px;
}

.p-autocomplete-overlay.overlay .song:hover {
    background-color: var(--backcore-color1);
}

.p-autocomplete-overlay.overlay .song-title, .song-title {
    font-weight: bold;
}

.p-autocomplete-overlay.overlay .song-artists, .song-artists {
    font-size: 12px;
}

.selected-songs {
    overflow-y: auto;
    max-height: 70%;
}

.selected-songs .selected-song .delete-icon {
    color: var(--font-color);
    cursor: pointer;
    padding-right: 10px;
}

.selected-songs .selected-song .delete-icon:hover {
    color: red;
}

.no-results {
    color: var(--font-color);
    font-style: italic;
    padding-left: 10px;
}
</style>
