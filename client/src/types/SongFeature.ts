export enum SongFeatureCategory {
    TEMPO = 0,
    ENERGY = 1,
    VALENCE = 2,
    DANCEABILITY = 3,
    SPEECHINESS = 4
};

export interface SongFeature {
    readonly category?: SongFeatureCategory;
    readonly value: number;
};