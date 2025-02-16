import apiClient from '@/services/axios'
import { userService } from '@/services/userService'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from "@/stores/user";

export const authService = {
    async authorize(username: string) {
        await apiClient.post('/token', {
            username: username
        }).then(async (response) => {
            await storeAuthorization(response.data?.['accessToken']);
            console.log('Logged in as guest with username: ' + username)
        })
    },

    async authorizeSpotify(authCode: string) {
        await apiClient.post('/auth-codes', {
            // Username will be populated by the BE.
            username: '',
            authCode
        }).then(async (response) => {
            await storeAuthorization(response.data?.['accessToken'], /* isHost= */true);
            console.log('Logged in via spotify with username')
        })
    }
}

const storeAuthorization = async function (token: string, isHost = false) {
    const authStore = useAuthStore()
    const userStore = useUserStore()

    if (token === undefined) {
        throw new Error('Authorization response did not include an access token.')
    }
    await authStore.authorize(token, isHost)

    const currentUser = authStore.user;
    console.log("current user: ", currentUser)
    if (currentUser) {
        // Add the new user to the host's user list
        userStore.addUser(currentUser);
        console.log('User added:', currentUser);
    } else {
        console.error('No user found in authStore after authorization.');
    }
}