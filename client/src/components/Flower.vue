<script setup lang ="ts">

import { computed, defineProps, defineEmits, useTemplateRef, onMounted} from 'vue';

import Petal from './Petal.vue';
import { SongFeature, SongFeatureCategory } from '@/types/SongFeature';

const props = defineProps<{
  features: SongFeature[];
  position?: {x: number, y: number};
  size?: number;
  circleRadius?: number;
  bloom?: boolean;
  mostSignificantFeature?: SongFeatureCategory
  isSelected?: boolean;
}>();

const emit = defineEmits(['onPetalClick', 'significantFeaturePosition', 'hover', 'leave']);


const size = props.size ?? 80;
const circleRadius = props.circleRadius ?? 40;

const maxPetalLength = computed(() => circleRadius + Math.max(...props.features.map(f => f.value * circleRadius)));
const center = computed(() => size / 2);
const rotation = computed(() => {
  const maxFeatureIndex = props.features.reduce(
      (maxIndex, feature, index, features) =>
          feature.value > features[maxIndex].value ? index : maxIndex,
      0
  );
  return (maxFeatureIndex * 360) / props.features.length;
});

const flower = useTemplateRef('flower');

const onPetalEndPositionComputed = (position, songFeatureCategory) => {
  if (songFeatureCategory === props.mostSignificantFeature) {
    emit('significantFeaturePosition', position);
  }
};

const bloomClass = computed(() => {
  if (props.bloom && !props.isSelected) return 'bloom-circle'; // bloom
  if (props.isSelected && !props.bloom) return 'bloom-static';   // Static bloom
  if (props.bloom && props.isSelected) return 'bloom-circle';  // bloom when both are true
  return ''; // No bloom effect
});

onMounted(() => {
  if (props.mostSignificantFeature === null) {
    emit('significantFeaturePosition', {x: maxPetalLength.value, y: maxPetalLength.value});
  }
  console.log(props.position);
});


</script>

<template>
  <svg
    class="flower"
    pointer-events="all"
    ref="flower"
    :x="position?.x"
    :y="position?.y"
    :width="maxPetalLength * 2"
    :height="maxPetalLength * 2"
    @mouseenter="() => emit('hover')"
    @mouseleave="() => emit('leave')">
    
    <!-- Define the glowing effect -->
    <defs>
      <filter id="circle-bloom">
        <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur1" />
        <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="blur2" />
        <feMerge result="combinedBlur">
          <feMergeNode in="blur1" />
          <feMergeNode in="blur2" />
        </feMerge>
        <feColorMatrix type="matrix" values="8 0 0 0 0  0 8 0 0 0  0 0 8 0 0  0 0 0 1 0" result="brightBlur" />
        <feComposite in="brightBlur" in2="SourceGraphic" operator="arithmetic" k1="1" k2="1" k3="0" k4="0" result="compositeGlow" />
        <feMerge>
          <feMergeNode in="compositeGlow" />
          <feMergeNode in="brightBlur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    
    <circle
        :cx="maxPetalLength"
        :cy="maxPetalLength"
        :r="circleRadius"
        fill="none"
        stroke="#CCCCCC"
        stroke-width="1"
        :class="bloomClass"
    />
    <Petal
        class="petal"
        v-for="(feature, index) in props.features"
        :key="index"
        :index="index"
        :feature="feature"
        :center="maxPetalLength"
        :circleRadius="circleRadius"
        :rotation="rotation"
        @click="() => emit('onPetalClick', feature.category)"
        @emitEndPosition="(position) => onPetalEndPositionComputed(position, feature.category)"
      />

  </svg>
</template>


<style scoped>
svg {
  display: block;
  margin: auto;
}

.petal {
  cursor: pointer;
}

@keyframes bloom {
  0%, 100% {
    filter: url(#circle-bloom);
  }
  50% {
    filter: url(#circle-bloom-strong);
  }
}

.bloom-circle {
  animation: bloom 1s infinite ease-in-out;
  filter: url(#circle-bloom);
}
.bloom-static {
  filter: url(#circle-bloom);
}
.flower {
  cursor: pointer;
}
</style>
