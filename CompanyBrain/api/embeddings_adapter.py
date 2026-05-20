import os
import hashlib
import random
import math

# Minimal embeddings adapter with three providers: local (pseudo), openai (placeholder), hf (placeholder)
# Real implementations should add proper clients and error handling.

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

class EmbeddingsAdapter:
    def __init__(self, provider: str = None, dim: int = 768):
        self.provider = provider or os.getenv('EMBEDDINGS_PROVIDER', 'local')
        self.dim = dim

    def embed_text(self, text: str):
        """Return a vector for text. """
        if self.provider == 'local':
            return self._local_embed(text)
        elif self.provider == 'openai':
            # Placeholder: integrate OpenAI SDK (openai.Client) in production.
            return self._local_embed(text)
        elif self.provider == 'hf':
            # Placeholder: integrate huggingface inference or sentence-transformers.
            return self._local_embed(text)
        else:
            return self._local_embed(text)

    def _local_embed(self, text: str):
        # Deterministic pseudo-embedding using sha256 => seed for RNG
        h = int(_sha256(text)[:16], 16)
        rnd = random.Random(h)
        return [rnd.uniform(-1, 1) for _ in range(self.dim)]

    @staticmethod
    def cosine_similarity(a, b):
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return sum(x*y for x,y in zip(a,b)) / (na * nb)
