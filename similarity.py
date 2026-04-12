"""
similarity.py — AI Matching Engine
===================================
This module handles ALL similarity logic for the recovery system.
It is imported by app.py and keeps the main app clean and readable.

Three components:
  1. TextSimilarity   — Sentence-BERT (fast, cached in RAM)
  2. ImageSimilarity  — CLIP (optional; cached in MongoDB)
  3. UnifiedScorer    — Combines scores: 0.5*text + 0.3*image + 0.2*route
"""

import hashlib
import logging
import os
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 1. TEXT SIMILARITY (Sentence-BERT)
# ──────────────────────────────────────────────
class TextSimilarity:
    """
    Wraps SentenceTransformer for semantic text similarity.

    Embeddings are cached in a plain dict (RAM cache) keyed by the
    MD5 hash of the input text. This means repeated calls with the
    same description are nearly instant (no GPU/CPU re-inference).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SBERT model: {model_name}")
        self.model = SentenceTransformer(model_name)
        # In-memory cache: { text_hash: embedding_ndarray }
        self._cache: dict = {}
        logger.info("SBERT model loaded ✓")

    def _hash(self, text: str) -> str:
        """Return MD5 hash of text (used as cache key)."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()

    def embed(self, text: str) -> np.ndarray:
        """
        Get embedding for a text string.
        Uses cache to avoid recomputing the same text twice.
        """
        key = self._hash(text)
        if key not in self._cache:
            self._cache[key] = self.model.encode([text])[0]
        return self._cache[key]

    def similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute cosine similarity between two texts.
        Returns a float in [0.0, 1.0].
        """
        if not text_a or not text_b:
            return 0.0
        emb_a = self.embed(text_a)
        emb_b = self.embed(text_b)
        score = cosine_similarity([emb_a], [emb_b])[0][0]
        return float(score)


# ──────────────────────────────────────────────
# 2. IMAGE SIMILARITY (CLIP)
# ──────────────────────────────────────────────
class ImageSimilarity:
    """
    Wraps OpenAI CLIP for visual image similarity.

    Embeddings are stored in MongoDB (image_embeddings collection) so
    that re-starting the server does NOT require re-running CLIP.
    If CLIP is unavailable (not installed / import error), all image
    scores gracefully return 0.0 and text+route scoring still works.
    """

    def __init__(self, db=None):
        """
        db: pymongo database object (for embedding cache collection).
        """
        self.db = db
        self.model = None
        self.processor = None
        self.available = False  # Will be True only if CLIP loads OK

        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            logger.info("Loading CLIP model (openai/clip-vit-base-patch32)…")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.eval()  # Inference mode (no gradient tracking needed)
            self.available = True
            logger.info("CLIP model loaded ✓")
        except Exception as e:
            logger.warning(
                f"CLIP unavailable — image scoring disabled. "
                f"Reason: {e}. "
                f"Install 'transformers' and 'torch' to enable it."
            )

    def _get_cached_embedding(self, image_path: str) -> Optional[np.ndarray]:
        """Look up a previously computed CLIP embedding in MongoDB."""
        if self.db is None:
            return None
        record = self.db["image_embeddings"].find_one({"image_path": image_path})
        if record and "embedding" in record:
            return np.array(record["embedding"], dtype=np.float32)
        return None

    def _save_embedding(self, image_path: str, embedding: np.ndarray):
        """Save a CLIP embedding to MongoDB for future reuse."""
        if self.db is None:
            return
        from datetime import datetime
        self.db["image_embeddings"].update_one(
            {"image_path": image_path},
            {"$set": {
                "image_path": image_path,
                "embedding": embedding.tolist(),
                "created_at": datetime.utcnow().isoformat()
            }},
            upsert=True   # Insert if not exists, update if exists
        )

    def embed(self, image_path: str) -> Optional[np.ndarray]:
        """
        Compute (or retrieve from cache) a CLIP embedding for an image file.
        image_path: absolute path to the image file on disk.
        Returns: numpy array of shape (512,) or None if CLIP unavailable.
        """
        if not self.available:
            return None

        # 1. Check MongoDB cache first
        cached = self._get_cached_embedding(image_path)
        if cached is not None:
            return cached

        # 2. Not cached — compute with CLIP
        try:
            import torch
            from PIL import Image

            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt")
            with torch.no_grad():
                features = self.model.get_image_features(**inputs)
                # Normalize to unit vector (cosine similarity works best this way)
                features = features / features.norm(dim=-1, keepdim=True)
            embedding = features[0].cpu().numpy()

            # 3. Save to MongoDB cache
            self._save_embedding(image_path, embedding)
            return embedding

        except Exception as e:
            logger.error(f"CLIP embedding failed for {image_path}: {e}")
            return None

    def similarity(self, path_a: str, path_b: str) -> float:
        """
        Compute cosine similarity between two image files.
        Returns float in [0.0, 1.0], or 0.0 if either image fails.
        """
        if not self.available or not path_a or not path_b:
            return 0.0
        emb_a = self.embed(path_a)
        emb_b = self.embed(path_b)
        if emb_a is None or emb_b is None:
            return 0.0
        score = cosine_similarity([emb_a], [emb_b])[0][0]
        return float(score)


# ──────────────────────────────────────────────
# 3. UNIFIED SCORER
# ──────────────────────────────────────────────
class UnifiedScorer:
    """
    Combines text, image, and route scores into a single match score.

    Formula:
        final_score = (0.5 × text_score)
                    + (0.3 × image_score)
                    + (0.2 × route_score)

    Weights rationale:
        - Text (0.5)  : Most reliable signal — descriptions are detailed
        - Image (0.3) : Strong visual evidence when available
        - Route (0.2) : Binary pass/fail based on route logic

    route_score is always 1.0 or 0.0 (boolean route eligibility).
    When no image is provided, image_score = 0.0 (weight redistributed
    implicitly — text becomes the dominant factor).
    """

    # Minimum final score to consider a report a "match"
    MATCH_THRESHOLD = 0.30

    @staticmethod
    def compute(
        text_score: float,
        image_score: float,
        route_score: float
    ) -> dict:
        """
        Compute unified score and return a breakdown dict.

        Returns:
            {
              "text":   0.72,
              "image":  0.65,
              "route":  1.0,
              "final":  0.70,
              "is_match": True
            }
        """
        final = (0.5 * text_score) + (0.3 * image_score) + (0.2 * route_score)
        final = round(float(final), 4)
        return {
            "text":     round(float(text_score), 4),
            "image":    round(float(image_score), 4),
            "route":    round(float(route_score), 4),
            "final":    final,
            "is_match": final >= UnifiedScorer.MATCH_THRESHOLD
        }
