from sentence_transformers import SentenceTransformer, util
import torch

class SemanticMatcher:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticMatcher, cls).__new__(cls)
            
            # On Windows/Development, avoid loading the heavy model in the monitor process
            import os
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or os.environ.get('FLASK_ENV') == 'production':
                print("[AI] Loading Semantic Matcher model (all-MiniLM-L6-v2) in main process...")
                cls._model = SentenceTransformer('all-MiniLM-L6-v2')
                if torch.cuda.is_available():
                    cls._model = cls._model.to('cuda')
            else:
                print("[AI] Semantic Matcher standby (reloader monitor).")
                cls._model = None
        return cls._instance

    def get_similarity(self, text1, text2):
        """Returns a similarity score between 0 and 1."""
        if not text1 or not text2:
            return 0.0
            
        embeddings1 = self._model.encode(text1, convert_to_tensor=True)
        embeddings2 = self._model.encode(text2, convert_to_tensor=True)
        
        cosine_scores = util.cos_sim(embeddings1, embeddings2)
        return float(cosine_scores[0][0])

    def find_matches(self, lost_desc, found_items, threshold=0.4):
        """
        Filters and sorts found items based on semantic similarity to lost description.
        found_items: list of dicts, each with 'description' field.
        """
        if not lost_desc or not found_items:
            return []

        # Encode lost description
        lost_emb = self._model.encode(lost_desc, convert_to_tensor=True)
        
        # Encode all found descriptions
        found_descs = [item.get('description', '') for item in found_items]
        found_embs = self._model.encode(found_descs, convert_to_tensor=True)
        
        # Compute cosine similarities
        cosine_scores = util.cos_sim(lost_emb, found_embs)[0]
        
        results = []
        for i, score in enumerate(cosine_scores):
            score_val = float(score)
            if score_val >= threshold:
                item = found_items[i].copy()
                item['match_score'] = round(score_val * 100, 1)
                results.append(item)
        
        # Sort by score descending
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results

# Initialize the matcher
matcher = SemanticMatcher()
