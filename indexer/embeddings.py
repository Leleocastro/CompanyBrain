import hashlib
import math
from typing import List

class EmbeddingProvider:
    """Simple embedding adapter with providers: 'mock' (default), placeholder for 'openai','hf','local'.

    The mock provider returns deterministic fixed-size vectors computed from sha256 hex digest.
    """

    def __init__(self, provider: str = None):
        self.provider = provider or ("mock")
        self.dim = 64

    def _mock_embed(self, text: str) -> List[float]:
        # Deterministic pseudo-embedding from sha256 hex digest
        h = hashlib.sha256(text.encode('utf-8')).hexdigest()
        # convert hex pairs to numbers, fold/truncate to dim
        nums = [int(h[i:i+2], 16) for i in range(0, min(len(h), self.dim*2), 2)]
        # if too short, repeat
        while len(nums) < self.dim:
            nums += nums
        nums = nums[:self.dim]
        # normalize to unit vector
        norm = math.sqrt(sum(x*x for x in nums)) or 1.0
        return [x / norm for x in nums]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self.provider == 'mock':
            return [self._mock_embed(t) for t in texts]
        else:
            raise NotImplementedError(f"Provider '{self.provider}' not implemented in this MVP adapter")


# utility

def cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x,y in zip(a,b))
