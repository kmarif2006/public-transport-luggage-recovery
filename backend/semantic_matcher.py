"""
Tamil Nadu Bus Lost Luggage — Semantic Matcher
Model : all-MiniLM-L6-v2  (sentence-transformers)
Scoring: 60% semantic cosine + 20% fuzzy keyword + 20% route proximity
"""

import os
from sentence_transformers import SentenceTransformer, util
from thefuzz import fuzz
import torch


class SemanticMatcher:
    """
    Singleton semantic matcher.
    Skips model load in Werkzeug's reloader monitor process to avoid double-loading.
    """
    _instance = None
    _model    = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            in_main = (
                os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or
                os.environ.get('FLASK_ENV') == 'production'
            )
            if in_main:
                print('[AI] Loading Semantic Matcher (all-MiniLM-L6-v2)...')
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
                if torch.cuda.is_available():
                    cls._model = cls._model.to('cuda')
                print('[AI] Semantic Matcher ready.')
            else:
                print('[AI] Semantic Matcher standby (reloader monitor).')
        return cls._instance

    # ------------------------------------------------------------------
    # PRIVATE HELPERS
    # ------------------------------------------------------------------

    def _semantic_score(self, lost_emb, found_emb) -> float:
        """Cosine similarity in [0, 1]."""
        score = util.cos_sim(lost_emb, found_emb)
        return max(0.0, float(score[0][0]))

    def _fuzzy_score(self, lost_text: str, found_text: str) -> float:
        """Fuzzy token-set ratio normalised to [0, 1]."""
        if not lost_text or not found_text:
            return 0.0
        return fuzz.token_set_ratio(lost_text.lower(), found_text.lower()) / 100.0

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def get_similarity(self, text1: str, text2: str) -> float:
        """
        Simple pairwise semantic similarity (backward-compat).
        Returns float in [0, 1].
        """
        if not self._model or not text1 or not text2:
            return 0.0
        e1 = self._model.encode(text1, convert_to_tensor=True)
        e2 = self._model.encode(text2, convert_to_tensor=True)
        return self._semantic_score(e1, e2)

    def find_matches(self, lost_desc: str, found_items: list, threshold: float = 0.35) -> list:
        """
        Backward-compatible basic matching (semantic only).
        """
        return self.find_matches_advanced(lost_desc, found_items, route_depots=[], threshold=threshold)

    def find_matches_advanced(
        self,
        lost_desc  : str,
        found_items: list,
        route_depots: list = None,
        threshold  : float = 0.20,
    ) -> list:
        """
        Multi-signal matching.

        Score = 0.60 × semantic_cosine
              + 0.20 × fuzzy_keyword_overlap
              + 0.20 × route_proximity_bonus

        Args:
            lost_desc    : Description string from passenger's report.
            found_items  : List of dicts, each with at least a 'description' key.
            route_depots : List of depot_ids along the passenger's travel path.
            threshold    : Minimum combined score to include in results.

        Returns:
            List of enriched found-item dicts with 'match_score' (0–100).
        """
        if not self._model or not lost_desc or not found_items:
            return []

        route_set = set(route_depots or [])

        # Batch encode lost description
        lost_emb = self._model.encode(lost_desc, convert_to_tensor=True)

        # Batch encode all found descriptions
        found_descs = [item.get('description', '') for item in found_items]
        found_embs  = self._model.encode(found_descs, convert_to_tensor=True)

        results = []
        for i, (item, found_emb, found_text) in enumerate(
            zip(found_items, found_embs, found_descs)
        ):
            # --- Component scores ---
            sem   = self._semantic_score(
                lost_emb.unsqueeze(0),
                found_emb.unsqueeze(0),
            )
            fuzzy = self._fuzzy_score(lost_desc, found_text)

            # Route proximity: +1 if depot is on the travel path, 0 otherwise
            item_depot    = item.get('depot_id', '')
            route_bonus   = 1.0 if item_depot and item_depot in route_set else 0.0

            # --- Weighted combination ---
            combined = (0.60 * sem) + (0.20 * fuzzy) + (0.20 * route_bonus)

            if combined >= threshold:
                enriched = item.copy()
                enriched['match_score']         = round(combined * 100, 1)
                enriched['_score_semantic']     = round(sem   * 100, 1)
                enriched['_score_fuzzy']        = round(fuzzy * 100, 1)
                enriched['_score_route_bonus']  = int(route_bonus * 100)
                results.append(enriched)

        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results


# Module-level singleton — imported by luggage and manager routes
matcher = SemanticMatcher()
