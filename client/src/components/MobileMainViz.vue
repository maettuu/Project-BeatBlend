<script setup lang="ts">
import Flower from "@/components/Flower.vue";
import {Session} from '@/types/Session';
import {SongFeatureCategory} from '@/types/SongFeature';
import { getSongFeatures, sessionService } from "@/services/sessionService";
import {ref, onMounted, onUnmounted, computed} from 'vue';
import {useAuthStore} from "@/stores/auth";
import {useSession} from "@/stores/session";

const props = defineProps<{
  session: Session,
}>();

const countdownDelta = ref(0);
const isTimeUp = ref(false);

const countdown = computed(() => {
  console.log(props.session);
  const millis = Date.now() - new Date(props.session.votingStartTime);
  console.log(millis / 1000);
  countdownDelta.value = 0;
  isTimeUp.value = false;
  return Math.floor(Math.max(20 - millis / 1000, 0));
});

let timer: NodeJS.Timeout | null = null;

const authStore = useAuthStore();
const user = authStore.user;

const selectedVote = computed(() => {
  const index = props.session.recommendations.findIndex((recommendation) => recommendation.votes.includes(user.id));
  if (index === -1) {
    return null;
  }

  return index;
})

const removedFromSession = computed(() => {
  return !Object.keys(props.session.guests).includes(user.id);
});

const songList = computed(() => {
  return props.session.recommendations.map((song) => {
    return {
      id: song.id,
      title: song.trackName,
      artist: song.artists.join(', '),
      features: getSongFeatures(song)
    };
  });
});

const handleVote = async (songIndex: number) => {
  const songId = songList.value[songIndex].id;
  if (selectedVote.value === songIndex) {
    await sessionService.deleteVote(props.session.id, songId);
  } else {
    await sessionService.addVote(props.session.id, songId);
  }
};

// Countdown logic
onMounted(() => {
  timer = setInterval(() => {
    if (countdown.value - countdownDelta.value > 0) {
      countdownDelta.value += 1;
    } else {
      isTimeUp.value = true; // Show popup when countdown reaches 0
    }
  }, 1000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<template>
  <div v-if="removedFromSession">
    You were removed from this session.
  </div>
  <div v-else-if="!props.session.votingStartTime">
   <div class="sticky-header">
      <h2 class="header">No recommendations yet</h2>
    </div>
  </div>
  <div v-else-if="props.session.votingStartTime" class="mobile-visualization">
    <div class="sticky-header">
      <h2 class="header">Vote for the next song!</h2>
      <p class="countdown">Time remaining: {{ countdown - countdownDelta }}s</p>
    </div>
    <div class="song-list">
      <div v-for="(song, index) in songList" :key="index" class="song-item">
        <Flower :features="song.features" :size="80" :circleRadius="40" />
        <div class="song-details">
          <p class="song-title">{{ song.title }}</p>
          <p class="song-artist">{{ song.artist }}</p>
        </div>
        <div class="vote-controls">
          <button
            :class="{ active: selectedVote === index }"
            @click="handleVote(index)"
          >
            <i class="pi pi-thumbs-up"></i>
          </button>
        </div>
      </div>
    </div>
    <div v-if="isTimeUp" class="popup">
      <div class="popup-content">
        <p class="line1">Time up!</p>
        <p class="line2">Your vote has been collected!</p>
      </div>
    </div>
  </div>
</template>


<style scoped>
.mobile-visualization {
  text-align: center;
  color: white;
  overflow: auto;
}

.sticky-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: #272525;
}

.header {
  font-size: 18px;
  margin-top: 0;
  margin-bottom: 5px;
}

.countdown {
  font-size: 16px;
  margin-bottom: 5px;
  color: #FFCC00;
}

.song-list {
  display: flex;
  flex-direction: column;
  padding-left: 5px;
}

.song-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 0;
}

.song-details {
  flex: 1;
  padding-left: 5px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.song-title, .song-artist {
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.vote-controls {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.vote-controls button {
  background: none;
  border: none;
  font-size: 24px;
  color: white;
  cursor: pointer;
}

.vote-controls button.active {
  color: #6AA834;
}

.popup {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.popup-content {
  background: #363636;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  font-weight: bold;
}

.line1 {
  font-size: 18px;
  color: #FFCC00;
}

.line2 {
  font-size: 16px;
  color: #FFF;
}
</style>
