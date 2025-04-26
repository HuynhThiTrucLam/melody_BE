import librosa
import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.tracks import Track, TrackItem

# Initialize text embedding model
text_model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_audio_features(audio_path):
    """Extract key audio features using librosa"""
    # Load audio file
    y, sr = librosa.load(audio_path)

    # Extract features
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # Aggregate features (mean across time)
    features = np.hstack(
        [
            np.mean(mfcc, axis=1),
            np.mean(chroma, axis=1),
            np.mean(spectral_contrast, axis=1),
            [tempo / 200.0],  # Normalize tempo
        ]
    )

    return features


def create_metadata_embedding(song_metadata: Track):
    """Create text embeddings from song metadata"""
    # Combine relevant metadata
    text = f"{song_metadata.name} {song_metadata.artists.items[0].profile.name} {song_metadata.albumOfTrack.name}"
    # Create embedding
    embedding = text_model.encode(text)
    return embedding


def create_hybrid_embedding(song_metadata: Track, audio_path: str = None):
    """Create a combined embedding using both audio and metadata"""
    # Get metadata embedding
    metadata_embedding = create_metadata_embedding(song_metadata)
    metadata_embedding_normalized = metadata_embedding / np.linalg.norm(
        metadata_embedding
    )

    # If audio path is provided, include audio features
    if audio_path:
        audio_features = extract_audio_features(audio_path)
        audio_features_normalized = audio_features / np.linalg.norm(audio_features)

        # Dimensionality reduction might be needed if dimensions differ significantly
        # For simplicity, we'll concatenate and assume appropriate normalization
        hybrid_embedding = np.concatenate(
            [
                audio_features_normalized * 0.4,  # 40% weight to audio features
                metadata_embedding_normalized * 0.6,  # 60% weight to metadata
            ]
        )
    else:
        # Fall back to just metadata if no audio
        hybrid_embedding = metadata_embedding_normalized

    # Return as a regular Python list for MongoDB compatibility
    return hybrid_embedding.tolist()
