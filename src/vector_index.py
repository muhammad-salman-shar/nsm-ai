"""Fast CPU/SIMD in-RAM semantic & character n-gram vector index (Two-Tier Hot Cache)."""

import hashlib
import re
import threading
from typing import Dict, List, Optional, Tuple

import numpy as np

_WORD_RE = re.compile(r"[a-z0-9_']+")

STOP_WORDS = frozenset({
    "a", "an", "the", "is", "am", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "about", "as", "into",
    "this", "that", "these", "those", "it", "its", "and", "or", "but", "if",
    "then", "so", "do", "does", "did", "very", "just", "really", "hai", "hain",
    "ka", "ki", "ke", "ko", "mein", "me", "se", "par", "pe", "aur", "ya", "bhi",
})


def extract_features(text: str) -> List[Tuple[str, float]]:
    """Extract weighted word unigrams, bigrams, and character n-grams for robust matching."""
    if not text:
        return []
    lowered = text.lower().strip()
    words = _WORD_RE.findall(lowered)
    if not words:
        return []

    features: List[Tuple[str, float]] = []
    content_words = [w for w in words if w not in STOP_WORDS or len(words) <= 2]
    if not content_words:
        content_words = words

    for w in content_words:
        # Word unigram (highest weight)
        features.append((f"w:{w}", 2.0))
        # Stem-like prefix for morphology/inflection matching
        if len(w) >= 5:
            features.append((f"p:{w[:4]}", 1.1))
        # Character 3-grams and 4-grams (handles typos and Hinglish/English variants)
        padded = f"^{w}$"
        if len(padded) >= 4:
            for i in range(len(padded) - 2):
                features.append((f"c3:{padded[i:i+3]}", 0.55))
        if len(padded) >= 5:
            for i in range(len(padded) - 3):
                features.append((f"c4:{padded[i:i+4]}", 0.70))

    # Word bigrams capture phrase order & local context
    for i in range(len(content_words) - 1):
        features.append((f"b:{content_words[i]}_{content_words[i+1]}", 1.5))

    return features


def encode_text(text: str, dim: int = 256) -> np.ndarray:
    """Deterministically encode text into a normalized float32 hypervector."""
    vec = np.zeros(dim, dtype=np.float32)
    features = extract_features(text)
    if not features:
        return vec

    for feat, weight in features:
        digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        h = int.from_bytes(digest, "little")
        idx = h % dim
        sign = 1.0 if ((h >> 32) & 1) == 0 else -1.0
        vec[idx] += sign * weight

    norm = float(np.linalg.norm(vec))
    if norm > 1e-8:
        vec /= norm
    return vec


class FastVectorIndex:
    """In-memory vectorized cosine-similarity index for O(1) inserts and sub-ms search."""

    def __init__(self, dim: int = 256, max_hot_items: int = 5000):
        self.dim = dim
        self.max_hot_items = max_hot_items
        self._lock = threading.RLock()
        self._vec_map: Dict[str, np.ndarray] = {}
        self._text_map: Dict[str, str] = {}
        self._ids: List[str] = []
        self._matrix: Optional[np.ndarray] = None
        self._dirty: bool = True

    def __len__(self) -> int:
        return len(self._vec_map)

    def add(self, item_id: str, text: str) -> None:
        if not item_id or not text:
            return
        vec = encode_text(text, self.dim)
        if float(np.linalg.norm(vec)) < 1e-8:
            return
        with self._lock:
            self._vec_map[item_id] = vec
            self._text_map[item_id] = text
            # Enforce hot-cache memory cap (evict oldest entries cleanly)
            if len(self._vec_map) > self.max_hot_items:
                oldest_key = next(iter(self._vec_map))
                if oldest_key != item_id:
                    self._vec_map.pop(oldest_key, None)
                    self._text_map.pop(oldest_key, None)
            self._dirty = True

    def remove(self, item_id: str) -> None:
        with self._lock:
            if item_id in self._vec_map:
                self._vec_map.pop(item_id, None)
                self._text_map.pop(item_id, None)
                self._dirty = True

    def clear(self) -> None:
        with self._lock:
            self._vec_map.clear()
            self._text_map.clear()
            self._ids = []
            self._matrix = None
            self._dirty = True

    def _rebuild_matrix(self) -> None:
        if not self._vec_map:
            self._ids = []
            self._matrix = None
            self._dirty = False
            return
        self._ids = list(self._vec_map.keys())
        self._matrix = np.vstack([self._vec_map[k] for k in self._ids]).astype(np.float32)
        self._dirty = False

    def search(
        self,
        query: str,
        top_k: int = 8,
        min_score: float = 0.16,
    ) -> List[Tuple[str, float]]:
        q_vec = encode_text(query, self.dim)
        if float(np.linalg.norm(q_vec)) < 1e-8:
            return []

        with self._lock:
            if not self._vec_map:
                return []
            if self._dirty:
                self._rebuild_matrix()
            if self._matrix is None or len(self._ids) == 0:
                return []

            scores = self._matrix @ q_vec
            if top_k >= len(scores):
                order = np.argsort(-scores)
            else:
                part = np.argpartition(-scores, top_k)[:top_k]
                order = part[np.argsort(-scores[part])]

            results: List[Tuple[str, float]] = []
            for idx in order[:top_k]:
                sc = float(scores[idx])
                if sc >= min_score:
                    results.append((self._ids[int(idx)], round(sc, 4)))
            return results
