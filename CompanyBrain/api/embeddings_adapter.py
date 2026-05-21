import os
import hashlib
import random
import math
from openai import OpenAI


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingsAdapter:
    def __init__(self, provider: str = None, dim: int = 768):
        self.provider = provider or os.getenv("EMBEDDINGS_PROVIDER", "local")
        self.dim = dim
        self._openai_client = None

    def embed_text(self, text: str):
        """Return a vector for text."""
        if self.provider == "openai":
            return self._openai_embed(text)
        elif self.provider == "hf":
            return self._local_embed(text)
        else:
            return self._local_embed(text)

    def _openai_embed(self, text: str):
        client = self._openai_client or self._build_openai_client()
        model = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
        kwargs = {"model": model, "input": text}
        if model in ("text-embedding-3-small", "text-embedding-3-large"):
            kwargs["dimensions"] = self.dim
        resp = client.embeddings.create(**kwargs)
        return resp.data[0].embedding

    def _build_openai_client(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Set it to your OpenAI API key to use the 'openai' provider."
            )
        self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client

    def _local_embed(self, text: str):
        h = int(_sha256(text)[:16], 16)
        rnd = random.Random(h)
        return [rnd.uniform(-1, 1) for _ in range(self.dim)]

    @staticmethod
    def cosine_similarity(a, b):
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return sum(x * y for x, y in zip(a, b)) / (na * nb)
