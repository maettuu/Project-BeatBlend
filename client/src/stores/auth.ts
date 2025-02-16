import {defineStore} from 'pinia'
import {computed, ref} from 'vue'
import {User} from '@/types/User'
import router from '@/router'
import {jwtDecode} from 'jwt-decode'

export const useAuthStore = defineStore('auth', () => {
    const user = ref<User>()
    const token = ref<string>()

    //TODO: Probably needs some fixing (probably not only this variable)
    const authorized = computed<boolean>(() => {
        return token.value !== undefined
    })

    const storedUserData = localStorage.getItem('user')
    const storedToken = sessionStorage.getItem('token')
    if (storedUserData && storedToken) {
        user.value = new User(JSON.parse(storedUserData))
        console.log("USER", user.value);
        token.value = JSON.parse(storedToken)
    }

    const authorize = async function (access_token: string, isHost = false) {
        sessionStorage.setItem('token', JSON.stringify(access_token))
        token.value = access_token

        const decodedToken = jwtDecode<{sub: string, username: string}>(access_token)
        const authenticatedUser = new User({id: decodedToken.sub, username: decodedToken.username, isHost})
        localStorage.setItem('user', JSON.stringify(authenticatedUser))
        user.value = authenticatedUser
    }

    const deauthorize = async function () {
        user.value = undefined
        token.value = undefined
        sessionStorage.removeItem('token')
        localStorage.removeItem('user')
    }

    return {
        user,
        token,
        authorized,
        authorize,
        deauthorize
    }
})