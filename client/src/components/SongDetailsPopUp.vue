<template>
  <div class="song-detail-modal">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ song.trackName }}</h3>
      </div>
      <p><strong>Artist: </strong> {{ song.artists.join(', ') }}</p>
      <p><strong>Album: </strong> {{ song.album }}</p>
      <p><strong>Album Genres: </strong> {{ formattedGenres }}</p>
      <p><strong>Release Date: </strong> {{ formattedReleaseDate }}</p>
      <p><strong>Duration: </strong> {{ formattedDuration }}</p>
      <p><strong>Popularity: </strong> {{ computedPopularity }}/100 </p>
      <div class="add-by">
        <p><strong>Added By: </strong>
          <span v-if="addedByUser">
            {{ addedByUser.username }}
            <span id="avatar" class="avatar" v-html="addedByUser.avatar"></span>
          </span>
          <span v-else>Recommendation</span>
        </p>
      </div>
      <div class="votes" v-if="votedByUsers.length>0">
        <p><strong>Votes: </strong></p>
        <ul class="voter">
          <li v-for="user in  votedByUsers" :key="user.id">
            {{ user. username }}
            <span id="avatar" class="avatar" v-html="user.avatar"></span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useUserStore } from "@/stores/user.ts";

const props = defineProps({
  song: {
    type: Object,
    required: true
  },
});

// Format duration from milliseconds to minute:second format
const formatDuration = (durationMs) => {
  const minutes = Math.floor(durationMs / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
};

// Format release date to 'YYYY-MM-DD' format
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
};

// Computed properties for formatted values
const formattedDuration = formatDuration(props.song.durationMs);
const formattedReleaseDate = formatDate(props.song.releaseDate);

const formattedGenres = computed(() => {
  return props.song.genre && props.song.genre.length > 0 ? props.song.genre.join(', ') : 'Unknown';
});

const computedPopularity = computed(() =>{
  return props.song.popularity ? props.song.popularity : 0;
});

console.log("song info", props.song)

const userStore = useUserStore();

// Find the user who added the song based on their ID
const addedByUser = computed(() => {
  if (props.song.addedBy && props.song.addedBy.id) {
    console.log(props.song.addedBy);
    console.log("user id: ", props.song.addedBy.id);
    console.log("userStore: ", userStore.allUsers);
    console.log("store: ", userStore.users);
    console.log("id: ", userStore.findUser(props.song.addedBy.id));
    return userStore.findUser(props.song.addedBy.id);
  } else {
    console.log("props.song.addedBy is null or undefined");
    return null;
  }
});

const votedByUsers = computed(() => {
  if (props.song.votes) {
    return props.song.votes
        .map(id => userStore.findUser(id))
  }
  return [];
})
</script>

<style scoped>
.song-detail-modal {
  position: fixed;
  top: 35%;
  left: 87%;
  transform: translate(-50%, -50%);
  background-color: #272525;
  border-radius: 15px;
  padding: 10px;
  z-index: 1001;
  width: 70%;
  max-width: 300px;
  color: #D9D9D9;
  border: 2px solid #6AA834;
}

.modal-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0px 8px 0px;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
  word-wrap: break-word;
}

.add-by {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.votes {
  display: flex;
}

.voter {
  display: block;
  list-style-type: none;
  margin: 0;
  padding: 0;
}

.voter li{
  display: block;
}

.avatar {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-left: 10px;
}

p {
  margin: 0;
  font-size: 16px;
}

@media (max-width: 600px) {
  .song-detail-modal {
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 70%;
    padding: 15px;
  }

  .modal-header h3 {
    font-size: 16px;
  }

  p {
    font-size: 14px;
  }

  .modal-header button {
    font-size: 18px;
  }
}
</style>