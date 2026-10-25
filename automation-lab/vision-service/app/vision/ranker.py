"""
Ranker: Rank and filter ElementCandidate based on semantic similarity.
"""
import difflib
import re
from typing import List, Optional
from .models import ElementCandidate
from ..core.config import VisionConfig


def text_similarity(text1: str, text2: str, synonyms: Optional[List[str]] = None) -> float:
    """
    Compute normalized text similarity using token matching and SequenceMatcher.

    Args:
        text1: candidate text from OCR
        text2: target description
        synonyms: optional list of domain synonym words provided by caller

    Returns:
        Similarity score [0, 1]
    """
    if not text1 or not text2:
        return 0.0

    t1_lower = text1.lower().strip()
    t2_lower = text2.lower().strip()

    # Substring match
    if t1_lower in t2_lower or t2_lower in t1_lower:
        return 0.95

    seq_ratio = difflib.SequenceMatcher(None, t1_lower, t2_lower).ratio()

    # Token-level matching
    toks1 = [w for w in re.split(r"[\s\-_,.:;!?/()]+", t1_lower) if w]
    toks2 = [w for w in re.split(r"[\s\-_,.:;!?/()]+", t2_lower) if w]

    if not toks2:
        return seq_ratio

    syn_set = set(s.lower().strip() for s in (synonyms or []))
    target_synonyms = set(toks2) | syn_set

    matches = 0.0
    for t2 in toks2:
        best_match = 0.0
        for t1 in toks1:
            if t1 == t2:
                best_match = 1.0
                break
            elif t1 in syn_set and (t2 in syn_set or t2 in target_synonyms):
                best_match = max(best_match, 0.95)
            else:
                sim = difflib.SequenceMatcher(None, t1, t2).ratio()
                if sim >= 0.7:
                    best_match = max(best_match, sim)
        matches += best_match

    token_score = matches / len(toks2)
    return max(seq_ratio, token_score)


def rank_by_description(
    candidates: List[ElementCandidate],
    target_description: str,
    element_type: Optional[str] = None,
    synonyms: Optional[List[str]] = None,
    top_k: Optional[int] = None,
    confidence_threshold: float = VisionConfig.RANKING_MIN_RELEVANCE,
) -> List[ElementCandidate]:
    """
    Rank candidates by semantic similarity to target description.

    Args:
        candidates: list of ElementCandidate objects
        target_description: description of what we're looking for (e.g., "Add to cart")
        element_type: optional filter for element type (e.g., "button")
        synonyms: optional list of accepted synonym terms (e.g., ["bag", "carrito"])
        top_k: return top k candidates (default: return all above threshold)
        confidence_threshold: minimum relevance score to include

    Returns:
        Ranked list of candidates (sorted by relevance score descending)
    """
    if not candidates:
        return []

    scored = []

    for candidate in candidates:
        base_score = candidate.confidence_score

        text_sim = 0.0
        if candidate.semantic_text:
            text_sim = text_similarity(candidate.semantic_text, target_description, synonyms=synonyms)

        # Guard condition: If target_description is specified, reject candidates whose text
        # was read by OCR but has zero/near-zero similarity to the target (e.g. navigation headers, footers).
        # Candidates detected via 'template' without text (e.g. pure icon matching) are preserved.
        if candidate.semantic_text and text_sim < 0.25 and candidate.source_strategy != "template":
            continue

        type_bonus = 0.0
        if element_type and candidate.element_type == element_type:
            type_bonus = 0.1

        # If candidate has semantic text, text similarity scales the overall score to avoid false positives.
        if candidate.semantic_text:
            relevance_score = (base_score * 0.4 + text_sim * 0.5 + type_bonus) * (0.5 + 0.5 * text_sim)
        else:
            relevance_score = base_score * 0.7 + type_bonus

        scored.append({
            "candidate": candidate,
            "relevance_score": relevance_score,
            "text_similarity": text_sim,
            "base_score": base_score,
        })

    scored = [s for s in scored if s["relevance_score"] >= confidence_threshold]
    scored.sort(key=lambda x: x["relevance_score"], reverse=True)

    ranked_candidates = [s["candidate"] for s in scored]

    if top_k is not None:
        ranked_candidates = ranked_candidates[:top_k]

    return ranked_candidates
