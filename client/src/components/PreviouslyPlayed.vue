<template>
  <div class="song-table-container">
    <div class="song-table">
      <table>
        <thead>
          <tr>
            <th class="icon-header"></th>  <!-- Empty for the icon -->
            <th class="icon-header"></th>
            <th class="track-name">Track Name</th>
            <th>Artists</th>
            <th>Danceability</th>
            <th>Energy</th>
            <th>Speechiness</th>
            <th>Valence</th>
            <th>Tempo</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="song in props.songs" :key="song.id">
            <td class="icon-cell">
              <img src="../assets/table-play-icon.png" alt="play-icon" class="song-icon">
            </td>
            <td class="icon-cell" @click="showSongDetails(song)">
              <img src="../assets/eye-icon.svg" alt="eye-icon" class="eye-icon">
            </td>
            <td class="track-name">{{ song.trackName }}</td>
            <td>{{ song.artists.join(', ') }}</td>
            <td>{{ song.danceability }}</td>
            <td>{{ song.energy }}</td>
            <td>{{ song.speechiness }}</td>
            <td>{{ song.valence }}</td>
            <td>{{ song.tempo }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Song } from '@/types/Song';

const emit = defineEmits(['show-song-details']);

function showSongDetails(song) {
  emit('show-song-details', song);
}

const props = defineProps({
    songs: {
        type: Array,
        required: true
    }
});

</script>

<style scoped>
.song-table-container {
  background-color: #363636;
  padding: 0px 0px 5px 0px;
  border-radius: 15px;
  max-height: 500px;
}

.song-table {
  width: 100%;
  color: #D9D9D9;
}

.song-table table {
  width: 100%;
  border-collapse: collapse;
  border-radius: 15px;
  table-layout: fixed;
}
.song-table th {
  padding: 8px;
  text-align: center;
  word-wrap: break-word;
  border-bottom: 1px solid transparent;
  color: #D9D9D9;
  font-size: 15px;
  font-weight: bold;
  position: sticky;
  top: 0;
  background-color: #363636;
  z-index: 999;
}
.song-table td {
  padding: 8px;
  text-align: center;
  word-wrap: break-word;
  border-bottom: 1px solid transparent;
  color: #D9D9D9;
  font-size: 14px;
}

.song-table th.icon-header, .song-table td.icon-cell {
  width: 35px;
  text-align: center;
}

.song-table th.track-name, .song-table td.track-name {
  width: 220px;
}

.song-table img.song-icon {
  width: 20px;
  height: 20px;
  vertical-align: middle;
}

.song-table img.eye-icon {
  width: 20px;
  height: 20px;
  vertical-align: middle;
  filter: invert(1);
  transition: transform 0.3s ease, background-color 0.3s ease;
}

.song-table img.eye-icon:hover {
  background-color: #828282;
  border-radius: 25%;
  transform: scale(1.05);
}

@media (max-width: 600px) {
  .song-table-container {
    padding: 0;
    max-height: 300px;
  }

  .song-table th {
    font-size: 13px;
  }

  .song-table td {
    padding: 6px;
    font-size: 12px;
  }

  .song-table th.track-name, .song-table td.track-name {
    width: auto;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .song-table img.song-icon,
  .song-table img.eye-icon {
    width: 15px;
    height: 15px;
  }

  .song-table table {
    width: 800px;
  }
}
</style>