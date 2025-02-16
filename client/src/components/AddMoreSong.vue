<script setup lang="ts">
import { ref,computed, watch } from 'vue';
import Button from 'primevue/button';
import SongSelector from "@/components/SongSelector.vue";
import { Song } from '@/types/Song';
import { sessionService } from "@/services/sessionService";

const props = defineProps({
  onClosePopup: {
    type: Function,
    required: true,
  },
  sessionId: {
    type: String,
    required: true,
  },
});

const selectedSongs = ref([]);
const successMessageVisible = ref(false);
const status = ref("idle");

const canConfirm = computed(() => {
    return selectedSongs.value.length >= 1;
});

const addNewSongs = async () => {
  status.value = "loading";

  const results = await Promise.allSettled(
    selectedSongs.value.map(async (song) => {
        return sessionService.addSong(props.sessionId, song.id);
    })
  );

  selectedSongs.value = selectedSongs.value.filter((unused, index) => {
      return results[index].status !== "fulfilled";
  });

  status.value = "success";
}

</script>

<template>
  <div class="playlist-creator">
    <Button class="close-button" icon="pi pi-times" @click="props.onClosePopup" :unstyled="false" :disabled="status === 'loading'" />
    <div v-if="status !== 'idle'" class="status-screen">
      <div v-if="status === 'loading'" class="spinner"></div>
      <p v-else-if="status === 'success'" class="success-text">
        Songs added successfully!
      </p>
    </div>
    <SongSelector
      class="song-selector"
      v-model="selectedSongs"
      headerText="Add more songs to the playlist"
    />
    <Button
      class="start-session"
      :disabled="!canConfirm"
      @click="addNewSongs"
    >
      Confirm
    </Button>
  </div>
</template>

<style scoped>
.song-selector {
  margin-top: 20px;
}
.status-screen {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 250px;
  padding: 20px;
  background-color: #363636;
  border-radius: 12px;
  z-index: 100;
  color: white;
  font-size: 18px;
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

.success-text {
  font-size: 18px;
  font-weight: bold;
  color: #6BA149;
  white-space: nowrap;
}

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
  padding-top: 30px;
}

.close-button {
  position: absolute;
  top: 10px;
  right: 10px;
  background: transparent;
  border: none;
  border-radius: 25%;
  color: var(--font-color);
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 25px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.close-button:hover {
  background-color: var(--backcore-color1);
  color: #CCCCCC;
  transform: scale(1.07);
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
  color: #c4c4c4;
}

.success-message {
  position: absolute;
  bottom: 20px;
  left: 20px;
  color: #FFFFFF;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 16px;
  transition: opacity 0.3s ease;
}

.success-message.hidden {
  opacity: 0;
  visibility: hidden;
}
</style>