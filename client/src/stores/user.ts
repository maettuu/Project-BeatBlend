import { ref, computed, watch } from 'vue'
import { User } from '@/types/User'
import { defineStore } from 'pinia'
import { useSession } from "@/stores/session";

export const useUserStore = defineStore('userStore', () => {
    const users = ref<User[]>([]);
    const sessionStore = useSession();

    const populateUsersFromSession = () => {
        const sessionData = sessionStore.session;
        if (sessionData) {
            const hostUser = new User({
                id: sessionData.hostId,
                username: sessionData.hostName,
                isHost: true
            });
            const guestUsers = Object.keys(sessionData.guests || {}).map(key => new User ({
                id: sessionData.guests[key].id,
                username: sessionData.guests[key].username,
                isHost: false
            }));
            users.value = [hostUser, ...guestUsers];
        }
    };

    watch(() => sessionStore.session, populateUsersFromSession, { immediate: true })

    const addUser = (newUser: User) => {
        users.value.push(newUser)
    }

    const removeUser = (userId: string) => {
        users.value = users.value.filter(user => user.id !== userId)
    }

    const findUser = (userId: string): User | null => {
        return users.value.find((user) => user.id === userId) || null;
    }

    const allUsers = computed<User[]>(() => users.value)

    return {
        users,
        addUser,
        removeUser,
        findUser,
        allUsers
    }
})
