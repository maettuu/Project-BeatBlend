<script setup lang="ts">
import {onMounted, ref} from 'vue'
import {authService} from '@/services/authService'
import { useRouter } from 'vue-router'

const urlParams = new URLSearchParams(window.location.search)
const code = urlParams.get('code')

const router = useRouter();

onMounted(async () => {
  if (code != null) {
    await authService.authorizeSpotify(code)
        .then((response) => {
          router.push({name: 'home'});
        })
        .catch((error) => {
          console.log(error);
          router.push({name: 'landing'});
        })
  }
})

</script>
<template>
</template>