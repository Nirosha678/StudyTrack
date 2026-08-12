
import math
import re
from collections import Counter
from typing import List


_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "to", "of", "in", "on", "for", "with", "as", "at", "by", "from", "that",
    "this", "it", "its", "into", "using", "use", "uses", "used", "such",
    "these", "those", "you", "your", "we", "can", "will", "has", "have",
    "had", "not", "than", "then", "so", "which", "their", "each",
}


def _word_count(text: str) -> int:
    """Count words by splitting on whitespace -- used for the difficulty rule."""
    return len(text.split())


def summarize_notes(raw_text: str) -> dict:
   
    if raw_text is None:
        raw_text = ""

    stripped = raw_text.strip()

    # ---- Empty-input edge case ----
    if not stripped:
        return {
            "topic": "untitled",
            "key_points": [],
            "difficulty": "easy",  # word count is 0, which is < 40
        }

    # ---- topic: most frequent non-stopword word ----
    tokens = re.findall(r"[A-Za-z0-9]+", stripped.lower())
    meaningful_tokens = [t for t in tokens if t not in _STOPWORDS]
    if meaningful_tokens:
        counts = Counter(meaningful_tokens)
        # Counter.most_common(1) returns [(word, count)]; take the word.
        topic = counts.most_common(1)[0][0]
    else:
        
        topic = tokens[0] if tokens else "untitled"

    # ---- key_points: up to 3 non-empty sentences ----
    raw_sentences = re.split(r"[.!?]", stripped)
    key_points = []
    for sentence in raw_sentences:
        cleaned = sentence.strip()
        if cleaned:
            key_points.append(cleaned)
        if len(key_points) == 3:
            break

    # ---- difficulty: based on total word count ----
    total_words = _word_count(stripped)
    if total_words < 40:
        difficulty = "easy"
    elif total_words <= 100:
        difficulty = "medium"
    else:
        difficulty = "hard"

    return {
        "topic": topic,
        "key_points": key_points,
        "difficulty": difficulty,
    }


# ---------------------------------------------------------------------------
# Feature 2: mock embeddings + cosine similarity semantic search
# ---------------------------------------------------------------------------

VOCABULARY = [
    "sort", "search", "binary", "insertion", "sql", "join",
    "fastapi", "pydantic", "prompt", "llm", "database", "validate",
]


def _tokenize(text: str) -> List[str]:
  
    return re.findall(r"[a-z0-9]+", text.lower())


def mock_embed(text: str) -> List[float]:
    
    if text is None:
        text = ""
    tokens = _tokenize(text)
    token_counts = Counter(tokens)
    return [float(token_counts.get(word, 0)) for word in VOCABULARY]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


# ---------------------------------------------------------------------------
# Sample notes used by the semantic search endpoint
# ---------------------------------------------------------------------------

SAMPLE_NOTES = [
    {"id": 1, "text": "Binary search requires a sorted array and repeatedly halves the search range using a midpoint comparison."},
    {"id": 2, "text": "Insertion sort builds a sorted list one element at a time by shifting larger elements to the right."},
    {"id": 3, "text": "FastAPI uses Pydantic models to validate request bodies and automatically generates Swagger documentation."},
    {"id": 4, "text": "SQL joins combine rows from two tables using a matching column, such as inner join, left join, and full join."},
    {"id": 5, "text": "Prompt engineering structures a task, context, constraints, and desired output format to guide an LLM's response."},
]


def search_notes(query: str) -> List[dict]:
 
    query_vector = mock_embed(query)
    scored = []
    for note in SAMPLE_NOTES:
        note_vector = mock_embed(note["text"])
        score = cosine_similarity(query_vector, note_vector)
        scored.append({"id": note["id"], "text": note["text"], "score": score})

   
    scored.sort(key=lambda n: n["score"], reverse=True)
    return scored
