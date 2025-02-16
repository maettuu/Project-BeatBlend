<script setup lang="ts">
import {ref, watch, onMounted, computed} from 'vue';
import Flower from "@/components/Flower.vue";
import { Song } from "@/types/Song";
import { getSongFeatures, getSongFeatureCategory } from "@/services/sessionService";

const props = defineProps<{
  recommendations: Song[],
  zoomLevel: number,
  lastFlowerPosition?: {
    x: number,
    y: number,
  }
}>();

const emit = defineEmits(['hover', 'leave']);
const similarityScoreIndex = ref(-1);

const flowerData = computed(() => {
  return props.recommendations.map((song) => {
    return {
      features: getSongFeatures(song),
      mostSignificantFeature: getSongFeatureCategory(song.mostSignificantFeature),
      similarityScore: song.similarityScore,
    };
  });
});

const localFlowerLinePositions = ref({});
const flowerLines = computed(() => {
  const lines = [];
  const currentFlower = props.lastFlowerPosition;
  if (!currentFlower) {
    return [];
  }
  for (let i = 0; i < flowerData.value.length; i++) {
    const nextFlower = globalFlowerLinePositions(localFlowerLinePositions.value[i], flowerPositions.value[i]);
    if (!currentFlower || !nextFlower) {
      return [];
    }
    const positions = computeLineBetweenFlowers(currentFlower, nextFlower);
    lines.push({
      position: positions.line,
      width: 100 * (Math.max(flowerData.value[i].similarityScore, 0.95) - 0.95 + 0.01),
      textPosition: positions.text,
      similarityScore: Math.max(Math.trunc(flowerData.value[i].similarityScore * 1000) / 1000.0, 0)
    });
  }

  return lines;
});

const flowerPositions = computed(() => {
  if (!props.lastFlowerPosition) {
    return [];
  }
  const positions = [];
  const verticalDistance = -100;
  const horizontalDistance = 100;

  return props.recommendations.map((_, index) => {
    return {
      x: props.lastFlowerPosition.x + horizontalDistance,
      y: props.lastFlowerPosition.y - 40 - (index - 1) * verticalDistance,
    }
  })
});


const storeFlowerLinePosition = (position, index) => {
  localFlowerLinePositions.value[index] = position;
};

const globalFlowerLinePositions = (localPosition, gridPosition) => {
  if (!localPosition  || !gridPosition) {
    return null;
  }
  return {
    x: localPosition.x + gridPosition.x,
    y: localPosition.y + gridPosition.y,
  }; 
};

const curvatureRelativeIntensity = 50.0;

const shiftPoint = (a, b, p, distance) => {
    let dx = b.x - a.x;
    let dy = b.y - a.y;

    let perpendicularDx = -dy;
    let perpendicularDy = dx;

    let length = Math.sqrt(perpendicularDx * perpendicularDx + perpendicularDy * perpendicularDy);
    let unitPerpendicularDx = perpendicularDx / length;
    let unitPerpendicularDy = perpendicularDy / length;

    let newPx = p.x + unitPerpendicularDx * distance;
    let newPy = p.y + unitPerpendicularDy * distance;

    return { x: newPx, y: newPy };
};

const computeLineBetweenFlowers = (flowerA, flowerB) => {
  const convex = Math.random() > 0.5 ? 1 : -1;

  const firstCurvature = {
    x: (flowerB.x + flowerA.x) / 2,
    y: (flowerB.y + flowerA.y) / 2,
  };

  const distance = Math.abs(flowerB.x - flowerA.x) + Math.abs(flowerB.y - flowerA.y);
  const curvatureIntensity = distance * curvatureRelativeIntensity;

  const firstCurvatureShifted = shiftPoint(flowerA, flowerB, firstCurvature, curvatureRelativeIntensity);
  return {
    line: `M ${flowerA.x} ${flowerA.y}
      Q ${firstCurvatureShifted.x}
        ${firstCurvatureShifted.y},
        ${flowerB.x} ${flowerB.y}`,
    text: {
      ...firstCurvatureShifted
    }
  };
};

function toggleSimilarityScore(index) {
  if (similarityScoreIndex.value === index) {
    similarityScoreIndex.value = -1;
  } else if (similarityScoreIndex.value === -1) {
    similarityScoreIndex.value = index;
  }
}

</script>
<template>
    <Flower
      v-for="(flower, index) in flowerData"
      :features="flower.features"
      :mostSignificantFeature="flower.mostSignificantFeature"
      :circleRadius="30 * zoomLevel"
      :position="flowerPositions[index]"
      @significantFeaturePosition="(position) => storeFlowerLinePosition(position, index)"
      @hover="() => emit('hover', recommendations[index])"
      @leave="emit('leave')"
    />
    <g v-for="(line, index) in flowerLines" @mouseenter="() => toggleSimilarityScore(index)" @mouseleave="() => toggleSimilarityScore(index)">
      <path
        class="connecting-path"
        :d="line.position" stroke="white" :stroke-width="line.width" fill="transparent"
      />
      <text v-if="similarityScoreIndex === index" :x="line.textPosition.x" :y="line.textPosition.y" fill="white">{{line.similarityScore}}</text>
    </g>
</template>
<style scoped>
.flower-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
}
.song-details-container {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  max-width: 200px;
  white-space: nowrap;
}
.song-details {
  overflow: hidden;
  text-overflow: ellipsis;
}
.recommendations-wrapper {
  display: flex;
  flex-direction: row;
}
.connecting-path {
  cursor: pointer;
}
</style>