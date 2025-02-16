import { reactive, computed } from 'vue';

const MOBILE_MAX_WIDTH = 480;

// Layout service used to keep track of the page layout.
export const layoutService = reactive({
  windowSize: 0,
  onResize() {
    this.windowSize = window.innerWidth
  }
});

// Returns true if the current window size is on mobile.
export const isMobile = computed(() => layoutService.windowSize <= MOBILE_MAX_WIDTH);