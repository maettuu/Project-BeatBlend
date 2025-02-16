<script setup>
import { ref, computed, } from 'vue';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import SongSelector from "@/components/SongSelector.vue";
import { Song } from '@/types/Song';
import { Session } from "@/types/Session";
import { Playlist } from "@/types/Playlist";

const title = ref('');
const selectedSongs = ref([]);
const emit = defineEmits(['startSession']);
const loading = ref(false);

// True, if the session can be started.
// Currently, if the user selected at least 3 songs and a title.
const canStartSession = computed(() => {
    return selectedSongs.value.length >= 3 && title.value;
});

const startSession = async () => {
    loading.value = true;

    emit('startSession', new Session({
        name: title.value,
        playlist: new Playlist({
            playedSongs: [],
            currentSong: null,
            queuedSongs: selectedSongs.value,
        }),
    }));
};

</script>
<template>
    <div class="playlist-creator">
        <InputText class="title" type="text" v-model="title" placeholder="BeatBlend Title..." />
        <SongSelector
            v-model="selectedSongs"
            headerText="Add at least 3 songs to start the blend" />
        <Button class="start-session" :disabled="!canStartSession" @click="startSession">
            Start
        </Button>
        <div v-if="loading" class="loading-overlay">
            <div class="spinner"></div>
        </div>
    </div>
</template>

<style>

.playlist-creator {
    --margin-inline: 20px;
    background-color: var(--backcore-color3);
    width: min(700px, 90vw);
    height: min(600px, 60vh);
    display: flex;
    flex-direction: column;
    gap: 8px;
    border-radius: 20px;
    position: relative;
}

.title {
    margin: var(--margin-inline) 32px 5px;
    width: 70%;
    font-weight: 700;
    font-size: 25px;
    border: none;
}

.title, .songs input {
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
    width: min(30%, 300px);
}

.start-session {
    position: absolute;
    bottom: 20px;
    right: var(--margin-inline);
    font-size: 16px;
    background-color: var(--logo-highlight-color);
    border-radius: 12px;
    border: none;
    padding: 8px 20px;
    cursor: pointer;
    font-weight: bold;
    color: white;
}
.start-session:disabled {
    color: var(--button-disabled-font-color);
    background-color: var(--backcore-color1);
    border: 2px solid var(--logo-highlight-color);
    cursor: not-allowed;
}

.loading-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100px;
    height: 100px;
    background-color: #363636;
    border-radius: 12px;
    z-index: 1000;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
</style>
