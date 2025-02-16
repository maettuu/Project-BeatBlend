<script setup lang="ts">
import { ref } from 'vue';
import Flower from './Flower.vue';
import Petal from './Petal.vue';
import { SongFeature, SongFeatureCategory } from '@/types/SongFeature';

const showPopup = ref(true);

function closePopup(){
  showPopup.value = false;
}

</script>

<template>
  <div v-if="showPopup" class="popup-overlay">
    <div class="popup-content">
      <div class="popup-header">
        <h1>How to read the graph</h1>
        <button class="close-button" @click="$emit('close-popup')">✕</button>
      </div>
      <div class="popup-body">
        <div class="popup-column column-1">
          <div class="VizFontHeader" style="font-weight:bold; margin-left: 20px; margin-bottom: 20px;">
            Audio Features as Petals
          </div>
          <div class ="flower-ruler-container">
            <svg width="160" height="160">
              <circle cx="80" cy="80" r="40" fill="none" stroke="#FFFFFF" stroke-width="2"/>
              <Petal
                  :feature="{value: 0.5}"
                  :center="80"
                  :circleRadius="40"
                  fill="none"
              />
              <Petal
                  :feature="{value: 1.0}"
                  :center="80"
                  :circleRadius="40"
                  fill="none"
              />
            </svg>
            <div class="ruler">
              <div class="ruler-line"></div>
              <div class="horizontal-line" style="top: 0%;"></div>
              <div class="horizontal-line" style="top: 25%;"></div>
              <div class="horizontal-line" style="top: 50%;"></div>
              <div class="ruler-label" style="top: 0%;">1</div>
              <div class="ruler-label" style="top: 25%;">0.5</div>
              <div class="ruler-label" style="top: 50%;">0</div>
            </div>
          </div>
          <div class="petal-explanation">
            <p>Each petal represents an audio feature. The length and width are determined by the feature's value, ranging from 0 (center) to 1 (edge).</p>
          </div>
        </div>
        <div class="vertical-line"></div>
        <div class="popup-column column-2">
          <div class="VizFontHeader" style="font-weight:bold; margin-bottom: 20px;">
            Song as Flowers with Audio Feature Colors
          </div>
          <div class="flower-container">
            <Flower :features="[
              { value: 0.5, category: SongFeatureCategory.TEMPO },
              { value: 0.5, category: SongFeatureCategory.ENERGY },
              { value: 0.5, category: SongFeatureCategory.DANCEABILITY },
              { value: 0.5, category: SongFeatureCategory.SPEECHINESS },
              { value: 0.5, category: SongFeatureCategory.VALENCE }
            ]"/>
          </div>
          <div class="petal-descriptions-horizontal">
            <div class="petal-description">
              <div class="petal-color energy"></div>
              <p>Energy</p>
            </div>
            <div class="petal-description">
              <div class="petal-color danceability"></div>
              <p>Danceability</p>
            </div>
            <div class="petal-description">
              <div class="petal-color speechiness"></div>
              <p>Speechiness</p>
            </div>
            <div class="petal-description">
              <div class="petal-color valence"></div>
              <p>Valence</p>
            </div>
            <div class="petal-description">
              <div class="petal-color tempo"></div>
              <p>Tempo</p>
            </div>
          </div>
          <div class="horizontalLine"></div>
          <div class="popup-column column-3">
            <div class="VizFontHeader" style="font-weight:bold; margin-bottom: 20px;"> Linking of Flowers </div>
            <div class="popup-body" style="width:100%;">
              <div class="popup-column column-3">
                <div class ="petal-explanation">
                  <p>Flowers are linked by a connective line by their most significant audio features. The width of the line represents the strength of the connection.
                    By hovering over the line, it is possible to see the exact number. </p>
                </div>
                </div>
              </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>

.popup-content {
  background-color: var(--backcore-color1);
  border-radius: 8px;
  padding: 20px;
  width: 60%;
  max-width: 800px;
  color: white;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  position: sticky;
  top: 0;
  background-color: var(--backcore-color1);
  z-index: 1;
}

.popup-header h1 {
  margin: 20px;
  font-size: 24px;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  color: white;
  cursor: pointer;
}

.popup-body {
  display: flex;
  flex-direction: row;
  gap: 20px;
  overflow-y: auto;
  flex-grow: 1;
  align-items: flex-start;
  position: relative;

}

.popup-column {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.column-1 {
  flex: 1;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.column-2 {
  flex: 2;
  padding-left: 20px;
  padding-right: 10px;
  flex-direction: column;
  align-items: center;

}

.column-3 {
  flex: 1;
  width: 100%;
  display: flex;
  justify-content: center;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.VizFontHeader {
  margin: 5px;
  text-align: center;
  font-size: 16px;
}

.column-1::after {
  content: '';
  position: absolute;
  top: 10px;
  right: -50px;
  width: 1px;
  height: 130%;
  background-color: white;
}

.flower-ruler-container {
  position: relative;
  display: flex;
  align-items: center;
  margin-top: 8px;
}

.ruler {
  position: absolute;
  top: 0;
  right: 0px;
  height: 160px;
}

.ruler-line {
  width: 1px;
  height: 80px;
  background-color: #FFFFFF;
  position: absolute;
  top: 0;
  left: -10px;
}

.horizontal-line {
  width: 20px;
  height: 1px;
  background-color: #FFFFFF;
  position: absolute;
  left: -10px;
  transform: translateX(-50%);
}

.ruler-label {
  font-size: 12px;
  color: #FFFFFF;
  text-align: center;
  position: absolute;
  transform: translateY(-50%);
  left: 10px;
}

.petal-explanation {
  margin-left: 20px;
  text-align: center;
  font-size: 12px;
}

.flower-container {
  margin-bottom: 20px;

}

.petal-descriptions-horizontal {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  text-align: center;
  flex-wrap: wrap;
}

.petal-description {
  flex: 1 1 18%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.petal-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
}
.horizontalLine {
  width: 80%;
  height: 1px;
  margin: 20px 0;
  background-color: white;
  position: relative;
  z-index: 1 ;
  flex-shrink: 0;
}

@media (max-width: 840px) {
  .popup-body {
    flex-direction: column;
    align-items: flex-start;
    overflow-y: auto;
    position: relative;
  }
  .petal-explanation {
    margin-left: 40px;
    margin-right: 40px;
    text-align: center;
    font-size: 12px;
  }
  .column-2 {
    display: flex;
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
    width: 100%;
  }

  .vertical-line {
    width: 100%;
    height: 1px;
    margin: 20px 0;
    background-color: white;
    position: relative;
    z-index: 1 ;
    flex-shrink: 0;
  }
  .horizontalLine {
    width: 100%;
    height: 1px;
    margin: 20px 0;
    background-color: white;
    position: relative;
    z-index: 1 ;
    flex-shrink: 0;
  }
  .column-1::after {
    display: none;
  }
}
.tempo {
  background-color: var(--tempo-color);
}

.valence {
  background-color: var(--valence-color);
}

.speechiness {
  background-color: var(--speechiness-color);
}

.danceability {
  background-color: var(--danceability-color);
}

.energy {
  background-color: var(--energy-color);
}
</style>