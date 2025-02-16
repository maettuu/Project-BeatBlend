export class AverageFeatures {
    danceability: number;
    energy: number;
    speechiness: number;
    valence: number;
    scaledTempo: number;

    constructor(data: AverageFeatures) {
        this.danceability = data.danceability;
        this.energy = data.energy;
        this.speechiness = data.speechiness;
        this.valence = data.valence;
        this.scaledTempo = data.scaledTempo;
    }
}

export class Artifacts {
    songsPlayed: number;
    songsAddedManually: number;
    mostSongsAddedBy: string;
    mostVotesBy: string;
    mostSignificantFeatureOverall: string;
    firstRecommendationVotePercentage: number;
    averageFeatures: AverageFeatures;
    genreStart: string[];
    genreEnd: string[];

    constructor(data: Artifacts) {
        this.songsPlayed = data.songsPlayed;
        this.songsAddedManually = data.songsAddedManually;
        this.mostSongsAddedBy = data.mostSongsAddedBy;
        this.mostVotesBy = data.mostVotesBy;
        this.mostSignificantFeatureOverall = data.mostSignificantFeatureOverall;
        this.firstRecommendationVotePercentage = data.firstRecommendationVotePercentage;
        this.averageFeatures = new AverageFeatures(data.averageFeatures);
        this.genreStart = data.genreStart;
        this.genreEnd = data.genreEnd;
    }
}