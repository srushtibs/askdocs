from google import genai
from .config import settings

_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in batches. Returns 768-dim vectors."""
    out = []
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]
        res = _get_client().models.embed_content(
            model="gemini-embedding-001",
            contents=batch,
            config={"output_dimensionality": 768},
        )
        out.extend([e.values for e in res.embeddings])
    return out
