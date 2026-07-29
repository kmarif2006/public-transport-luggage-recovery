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
import requests
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
        logger.info("SBERT model loaded [OK]")

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
            logger.info("Loading CLIP model (openai/clip-vit-base-patch32)...")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model.eval()  # Inference mode (no gradient tracking needed)
            self.available = True
            logger.info("CLIP model loaded [OK]")
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
                
                # Handle old transformers version where it returns BaseModelOutputWithPooling
                if not isinstance(features, torch.Tensor) and hasattr(features, "pooler_output"):
                    features = features.pooler_output
                    
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
# 2.5 OCR EXTRACTOR (OCR.Space)
# ──────────────────────────────────────────────
class OCRExtractor:
    """
    Extracts text from images using the free OCR.Space API.
    """
    def __init__(self):
        self.api_key = os.environ.get("OCR_API_KEY")
        self.api_url = "https://api.ocr.space/parse/image"

        # Check if the placeholder is still there or if it's missing
        if not self.api_key or "YOUR_" in self.api_key:
            self.api_key = None
            logger.warning("OCR API key missing or invalid. OCR extraction disabled.")

    def extract_text(self, image_path: str) -> str:
        """
        Send image to OCR.Space and return the extracted text.
        """
        if not self.api_key or not os.path.exists(image_path):
            return ""

        try:
            with open(image_path, 'rb') as f:
                # We need to send the file as multipart/form-data
                payload = {
                    'apikey': self.api_key,
                    'language': 'eng',
                    'isOverlayRequired': False,
                    'scale': True
                }
                ext = os.path.splitext(image_path)[1].lower()
                mime_type = "image/png" if ext == ".png" else "image/jpeg"
                response = requests.post(
                    self.api_url,
                    files={'file': (os.path.basename(image_path), f, mime_type)},
                    data=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("IsErroredOnProcessing") == False:
                        # Combine text from all parsed results
                        parsed_text = " ".join([
                            r.get("ParsedText", "").replace('\r', '').replace('\n', ' ')
                            for r in result.get("ParsedResults", [])
                        ])
                        return parsed_text.strip().lower()
                    else:
                        logger.error(f"OCR API Error: {result.get('ErrorMessage')}")
        except Exception as e:
            logger.error(f"OCR Extraction failed for {image_path}: {e}")

        return ""

# ──────────────────────────────────────────────
# 2.6 OCR MATCH SCORING
# ──────────────────────────────────────────────
# Generic descriptors that must never, on their own, imply a match.
# (Only words longer than 4 chars are scored, so short words are already
#  excluded — this list catches the common *long* generic words.)
_OCR_STOPWORDS = {
    "black", "white", "brown", "green", "yellow", "orange", "purple",
    "golden", "silver", "colour", "color", "small", "large", "medium",
    "heavy", "light", "handbag", "luggage", "suitcase", "backpack",
    "wallet", "purse", "pouch", "cover", "strap", "zipper", "inside",
}


def ocr_match_score(name: str, description: str, ocr_text: str) -> float:
    """
    Score how strongly text read off the item (OCR) confirms a lost report.

    Why this is NOT a blunt 1.0 boost:
      A bag tag showing the passenger's full name is near-certain proof, so
      that still scores 1.0. But a single generic description word (e.g.
      "black") appearing on the bag is weak evidence and must not, by itself,
      clear the match threshold or trigger a high-confidence alert. So keyword
      hits are filtered (stop-words + length) and require corroboration:
        • full name found in OCR text      → 1.0  (strong)
        • 2+ distinct significant keywords  → 1.0  (strong)
        • exactly 1 significant keyword     → 0.4  (weak bonus)
        • otherwise                         → 0.0

    Returns a float in [0.0, 1.0].
    """
    if not ocr_text:
        return 0.0
    ocr_text = ocr_text.lower()

    name = (name or "").lower().strip()
    if len(name) >= 4 and name in ocr_text:
        return 1.0

    significant = {
        w for w in (description or "").lower().split()
        if len(w) > 4 and w.isalpha() and w not in _OCR_STOPWORDS
    }
    hits = sum(1 for w in significant if w in ocr_text)
    if hits >= 2:
        return 1.0
    if hits == 1:
        return 0.4
    return 0.0


# ──────────────────────────────────────────────
# 2.7 STRUCTURED (TRAVEL-RECORD) MATCH SCORING
# ──────────────────────────────────────────────
def _seat_num(v):
    """Best-effort parse of a seat value ('12', 'A5', 12) → int or None."""
    if v is None:
        return None
    import re as _re
    m = _re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def structured_match_score(found_trip_id, lost_trip_id,
                           found_bus_id, lost_bus_id,
                           found_seat, lost_seat) -> float:
    """
    Score exact travel-record evidence linking a found item to a lost report,
    using the transport database keys the passenger and depot now capture.

    Precedence (strongest wins):
        • same trip (route + bus + departure)  → 1.0  (near-proof)
        • same bus (different/absent trip)      → 0.6  (strong)
        • otherwise                              → 0.0
    Plus a small seat-proximity bonus (+0.15) when the item was found within
    two seats of where the passenger sat — but only if trip/bus already agree,
    so a seat number alone can never manufacture a match.

    Returns a float in [0.0, 1.0].
    """
    base = 0.0
    if found_trip_id and lost_trip_id and found_trip_id == lost_trip_id:
        base = 1.0
    elif found_bus_id and lost_bus_id and found_bus_id == lost_bus_id:
        base = 0.6

    if base > 0.0:
        fs, ls = _seat_num(found_seat), _seat_num(lost_seat)
        if fs is not None and ls is not None and abs(fs - ls) <= 2:
            base += 0.15

    return min(1.0, base)


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
                    + ocr_score
                    + structured_score

    Weights rationale:
        - Text (0.5)  : Most reliable signal — descriptions are detailed
        - Image (0.3) : Strong visual evidence when available
        - Route (0.2) : Binary pass/fail based on route logic
        - OCR (+1.0)  : If the passenger's name or exact description keywords are found on the bag, it's a guaranteed match.
        - Structured (+1.0) : Exact travel-record evidence from the transport DB
          (same trip / same bus / adjacent seat). A same-trip hit is near-proof,
          so it can clear the threshold on its own — mirrors the OCR full-name case.

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
        route_score: float,
        ocr_score: float = 0.0,
        structured_score: float = 0.0
    ) -> dict:
        """
        Compute unified score and return a breakdown dict.

        Returns:
            {
              "text":   0.72,
              "image":  0.65,
              "route":  1.0,
              "ocr":    0.0,
              "structured": 0.6,
              "final":  0.70,
              "is_match": True
            }
        """
        final = (
            (0.5 * text_score) + (0.3 * image_score) + (0.2 * route_score)
            + ocr_score + structured_score
        )
        # Cap at 1.0
        final = min(1.0, float(final))
        final = round(float(final), 4)
        return {
            "text":       round(float(text_score), 4),
            "image":      round(float(image_score), 4),
            "route":      round(float(route_score), 4),
            "ocr":        round(float(ocr_score), 4),
            "structured": round(float(structured_score), 4),
            "final":      final,
            "is_match": final >= UnifiedScorer.MATCH_THRESHOLD
        }
