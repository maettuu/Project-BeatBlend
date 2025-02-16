<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import { authService } from '@/services/authService';
import { useAuthStore } from '@/stores/auth';
import { sessionService } from '@/services/sessionService';
import LogoIntroScreen from "@/components/LogoIntroScreen.vue";
import { isMobile } from "@/services/layoutService";
import svgContent from '@/assets/circle-music-soundwave.svg';

const showStartScreen = ref(true);
const startAnimation = ref(false);
const showLogin = ref(false);
const username = ref<string>('');
const invitedSession = ref();
const hostUsername = computed(() => {
  return invitedSession.value ? invitedSession.value.hostName : "";
});

const router = useRouter();
const route = useRoute();

onMounted(async () => {
  setTimeout(() => {
    startAnimation.value = true;
    setTimeout(() => {
      showStartScreen.value = false;
      showLogin.value = true;
    }, 2000); // 2 seconds for animation before showing login
  }, 2000);

  await router.isReady();
  const sessionId = route.params.sessionId;
  if (sessionId) {
    invitedSession.value = await sessionService.getSessionById(sessionId);
  }
});

const redirectToSpotify = async () => {
  window.location.href = 'https://accounts.spotify.com/authorize?' +
      'response_type=' + 'code' +
      '&client_id=' + import.meta.env.VITE_SPOTIFY_CLIENT_ID +
      //'&scope' +
      '&redirect_uri=' + import.meta.env.VITE_SPOTIFY_REDIRECT_URI
      //'&state='
}

const handleComplete = () => {
  showStartScreen.value = false;
}

const joinSession = async (sessionId) => {
  if (!username.value) {
    return;
  }

  const authStore = useAuthStore();

  try {
    await authService.authorize(username.value);
    const guestSession = await sessionService.joinSession(sessionId);
    router.push({path: `/session/${guestSession.id}`});
  } catch (error) {
    console.log(error);
    await authStore.deauthorize();
  }
}

</script>

<template>
  <div>
    <transition name="fade" mode="out-in">
      <!-- Start Screen with SVG and Logo Animation -->
      <div v-if="showStartScreen" class="visualizer">
        <div :class="{ 'svg-container': true, 'svg-container-animation': startAnimation }" v-html="svgContent"></div>
        <div :class="{ 'text-overlay': true, 'text-overlay-animation': startAnimation }">
          <LogoIntroScreen :class="{ 'logo-animation': startAnimation}" />
        </div>
      </div>

      <!-- Login Screen with Logo and Login Button/Prompt -->
      <div v-else class="type1">
        <header class="header-container">
          <LogoIntroScreen class="logo-static" />
        </header>
        <div class="login-container" v-if="showLogin">
          <Button
            v-if="!$route.params.sessionId && !isMobile"
            class="button spotify-button"
            @click="redirectToSpotify"
          >
            Login via Spotify
          </Button>
          <div v-else-if="!$route.params.sessionId">
            Please use a computer to login as the host
          </div>
          <div v-else class="guest-login">
            <p class="invite-text">
              You have been invited to
              <span class="highlight">a new blend!</span>
            </p>
            <p class="host-info">
              <strong>{{ hostUsername }}</strong> invited you to the blend. Enter your username to join.
            </p>
            <InputText id="username" v-model="username" placeholder="Username" class="input-default" />
            <Button
              @click="() => joinSession($route.params.sessionId)"
              class="join-button"
              :disabled="!username.length"
            >
              Join
            </Button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>


<style scoped>
.visualizer {
  position: relative;
  width: 100vw;
  height: 100vh;
  background-color: var(--backcore-color1);
}

.svg-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: transform 2s ease-in-out;
}

.svg-container-animation {
  transform: scale(5);
}

.text-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 2em;
  transition: transform 2s ease-in-out;
}

.text-overlay-animation {
  transform: translate(-50%, -290%); /* Shift the text upward */
}

.logo-animation {
  transition: transform 1s ease-in-out, opacity 1s ease;
  transform: scale(0.8);
  position: relative;
}

.logo-static {
  transform: none;
  position: relative;
  width: auto;
  height: auto;
  font-size: 3em;
}

.header-container {
  display: flex;
  justify-content: center;
}

.login-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  width: 200px;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

.guest-login {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  background-color: var(--backcore-color3);
  border-radius: 10px;
  width: 200px;
  padding: 20px;
}

.invite-text {
  color: white;
  font-size: 16px;
  font-weight: bold;
  text-align: center;
}

.highlight {
  color: var(--logo-highlight-color);
}

.guest-login input {
  color: white;
}

.join-button {
  background-color: var(--logo-highlight-color);
  color: white;
  width: 80%;
  border: none;
  border-radius: 25px;
  font-size: 14px;
  height: 30px;
  font-weight: bold;
}

.join-button:disabled {
  color: var(--button-disabled-font-color);
}

.host-info {
  color: white;
  font-size: 14px;
  text-align: center;
}

.button {
  padding: 8px 16px;
  border: none;
  border-radius: 25px;
  font-size: 22px;
  font-weight: bold;
  cursor: pointer;
  width: 220px;
  height: 50px;
}

.spotify-button {
  background-color: var(--logo-highlight-color);
  color: white;
}
</style>