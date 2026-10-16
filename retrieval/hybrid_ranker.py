import re

def keyword_relevance(query: str, notes: str) -> float:
    """Baseline placeholder for semantic relevance; replace with embeddings in phase 2."""
    tokens = lambda s: set(re.findall(r"[a-z0-9]+", s.lower()))
    q = tokens(query)
    d = tokens(notes)
    if not q or not d:
        return 0.0
    return round(len(q & d) / len(q), 4)

def hybrid_score(relevance: float, latency_ms: float, urgency: str) -> float:
    """Combine normalized relevance and retrieval cost. Higher score ranks first."""
    latency_penalty = max(0.0, latency_ms) / (max(0.0, latency_ms) + 100.0)
    if urgency.upper() == "EMERGENCY":
        alpha, beta = 0.60, 0.40
    else:
        alpha, beta = 0.90, 0.10
    return round(alpha * relevance - beta * latency_penalty, 6)

def rank_candidates(query: str, rows: list[dict], urgency: str) -> list[dict]:
    ranked = []
    for row in rows:
        item = dict(row)
        relevance = keyword_relevance(query, item.get("notes", ""))
        latency = float(item.get("predicted_latency_ms") or 0)
        item["relevance_score"] = relevance
        item["hybrid_score"] = hybrid_score(relevance, latency, urgency)
        item["retrieval_warning"] = latency >= 15.0
        ranked.append(item)
    return sorted(ranked, key=lambda x: x["hybrid_score"], reverse=True)
