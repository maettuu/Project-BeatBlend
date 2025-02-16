<script setup>
import { computed } from 'vue';
import { Session } from "@/types/Session";
import moment from 'moment';

const props = defineProps({
    session: {
        type: Object,
        required: true
    }
});

const formattedDate = computed(() => {
    return moment(props.session.creationDate).format("MMMM Do YYYY, h:mm");
});

</script>

<template>
    <div class="session-item">
        <i class="pi pi-lock" v-if="!session.isRunning"></i>
        <i class="pi pi-circle" v-else></i>
        <span>{{props.session.name}}, {{formattedDate}}</span>
    </div>
</template>

<style scoped>
.session-item {
    color: var(--font-color-soft);
    padding: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
}
</style>
