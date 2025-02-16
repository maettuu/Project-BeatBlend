import avatar from 'animal-avatar-generator'

export class User {
    id: string
    username: string
    isHost: boolean
    avatar: string

    constructor(data: User) {
        this.id = data.id
        this.username = data.username
        this.isHost = data.isHost
        this.avatar = avatar(data.username, { size: 50 })
    }
}