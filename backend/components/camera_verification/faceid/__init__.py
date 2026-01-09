'''
Performs face scan verification, works by using the `face_recognition` module which uses a model that detects faces on images and produces their embeddings. The embeddings can then be easily compared to assess whether two faces match.

## Key Components

#### `faceidService.py`
- Contains the core logic for face recognition.
- Extracts facial features from images using pre-trained models.
- Compares extracted features with stored embeddings to determine identity matches.
- Provides utility functions for face detection, feature extraction, and similarity scoring.

'''