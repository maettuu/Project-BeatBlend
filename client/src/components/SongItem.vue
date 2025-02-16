<template>
  <div class="song-item">
    <i class="pi pi-play"></i>
    <div class="song-details">
      <span class="song-title">{{ song.trackName }}</span>
      <span class="song-artists">{{ combineArtists(song.artists) }}</span>
    </div>
    <div class="delete-container">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';

const props = defineProps({
  song: Object
});

const combineArtists = (artists) => {
  return artists.join(', ');
};
</script>

<style scoped>
.song-item {
  display: flex;
  flex-direction: row;
  justify-content: start;
  align-items: center;
  gap: 8px;
  color: var(--font-color);
  border-radius: 5px;
  padding: 5px;
  width: 100%;
}

.song-details {
  flex-grow: 1;    /*take up remaining space */
  display: flex;
  flex-direction: column;
  justify-content: start;
  gap: 2px;
}

.delete-container {
  margin-left: auto;
  padding-right: 10px;
}

.song-title {
  font-weight: bold;
}

.song-artists {
  font-size: 12px;
}
</style>
