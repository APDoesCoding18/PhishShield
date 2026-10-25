import os
import logging
from typing import Optional, Dict, Any, List
import joblib

logger = logging.getLogger(__name__)

class NLPInferenceService:
    """
    Singleton service for fast in-memory inference of the best-performing
    Classical NLP Model (TF-IDF + Calibrated Logistic Regression, 98.84% accuracy).
    """
    _instance: Optional["NLPInferenceService"] = None
    _pipeline = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPInferenceService, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        # Resolve path relative to backend root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # current_dir is backend/app/services/analyzers
        model_path = os.path.abspath(os.path.join(current_dir, "..", "..", "ml", "saved_models", "nlp_pipeline.joblib"))
        
        if not os.path.exists(model_path):
            # Fallback path if running from project root
            model_path = os.path.abspath(os.path.join("backend", "ml", "saved_models", "nlp_pipeline.joblib"))

        if os.path.exists(model_path):
            try:
                self._pipeline = joblib.load(model_path)
                logger.info(f"Loaded NLP model pipeline from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load NLP pipeline from {model_path}: {e}")
                self._pipeline = None
        else:
            logger.warning(f"NLP model pipeline not found at {model_path}")
            self._pipeline = None

    @property
    def is_ready(self) -> bool:
        return self._pipeline is not None

    def predict(self, text: str) -> Dict[str, Any]:
        """Predict phishing probability and explicitly report prediction status."""

        if not self.is_ready:
            logger.warning("NLP prediction unavailable: model is not loaded.")
            return {
                "status": "unavailable",
                "probability": None,
                "is_phishing": None,
                "confidence": None,
                "top_tokens": [],
                "error": "NLP model is not loaded.",
            }

        if not isinstance(text, str) or not text.strip():
            return {
                "status": "invalid_input",
                "probability": None,
                "is_phishing": None,
                "confidence": None,
                "top_tokens": [],
                "error": "Input text must be a non-empty string.",
            }

        try:
            probs = self._pipeline.predict_proba([text])[0]
            phishing_probability = float(probs[1])

            confidence = abs(phishing_probability - 0.5) * 2

            top_tokens = self._extract_top_tokens(text)

            return {
                "status": "success",
                "probability": phishing_probability,
                "is_phishing": phishing_probability >= 0.5,
                "confidence": float(confidence),
                "top_tokens": top_tokens,
                "error": None,
            }

        except Exception as exc:
            logger.exception("NLP prediction failed: %s", exc)

            return {
                "status": "error",
                "probability": None,
                "is_phishing": None,
                "confidence": None,
                "top_tokens": [],
                "error": "NLP prediction failed.",
            }
        
    def _extract_top_tokens(self, text: str, top_k: int = 5) -> List[str]:
        """Identifies tokens in the input that have high positive weights towards phishing."""
        try:
            tfidf = self._pipeline.named_steps.get("tfidf")
            clf = self._pipeline.named_steps.get("clf")
            if not tfidf or not clf:
                return []

            feature_names = tfidf.get_feature_names_out()
            coefs = clf.coef_[0]
            
            # Transform single text
            vec = tfidf.transform([text])
            nonzero_indices = vec.nonzero()[1]
            
            # Pair indices with (weight * tfidf_val)
            scored_terms = []
            for idx in nonzero_indices:
                weight = coefs[idx]
                if weight > 0:  # Only phishing-leaning tokens
                    scored_terms.append((feature_names[idx], weight * vec[0, idx]))
                    
            scored_terms.sort(key=lambda x: x[1], reverse=True)
            return [term for term, _ in scored_terms[:top_k]]
        except Exception:
            return []
