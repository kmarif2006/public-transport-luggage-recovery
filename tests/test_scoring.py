"""
Unit tests for the matching scorer logic.

These cover the pure scoring functions only — no database and no AI models are
loaded, so the suite runs in well under a second.

Run:  python tests/test_scoring.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from similarity import UnifiedScorer, ocr_match_score, structured_match_score


# ── OCR scoring (bug A2: generic words must not force a match) ────────────────
def test_ocr_single_generic_word_does_not_match():
    assert ocr_match_score("Ravi Kumar", "black bag", "black") == 0.0


def test_ocr_full_name_is_strong():
    assert ocr_match_score("Ravi Kumar", "blue bag", "property of ravi kumar") == 1.0


def test_ocr_single_distinctive_keyword_is_weak_bonus():
    assert ocr_match_score("Ravi", "lenovo laptop bag", "lenovo") == 0.4


def test_ocr_two_keywords_are_strong():
    assert ocr_match_score("Ravi", "lenovo thinkpad sleeve", "lenovo thinkpad") == 1.0


def test_ocr_empty_text():
    assert ocr_match_score("Ravi", "anything here", "") == 0.0


def test_generic_ocr_hit_does_not_auto_notify():
    # Regression for A2: a generic OCR hit must not push the final score to the
    # >= 0.80 line that fires an automatic WhatsApp alert.
    ocr = ocr_match_score("Ravi Kumar", "black bag", "black")
    score = UnifiedScorer.compute(text_score=0.2, image_score=0.0, route_score=1.0, ocr_score=ocr)
    assert score["final"] < 0.80


# ── Unified scorer (bug A3: single source of truth for the threshold) ─────────
def test_threshold_is_030():
    assert UnifiedScorer.MATCH_THRESHOLD == 0.30


def test_scorer_caps_at_one():
    score = UnifiedScorer.compute(1.0, 1.0, 1.0, ocr_score=1.0)
    assert score["final"] == 1.0
    assert score["is_match"] is True


def test_route_only_candidate_is_below_threshold():
    # Passing the route filter alone (route=1.0, nothing else) must NOT match.
    score = UnifiedScorer.compute(0.0, 0.0, 1.0, ocr_score=0.0)
    assert score["final"] < UnifiedScorer.MATCH_THRESHOLD


# ── Structured (travel-record) scoring ───────────────────────────────────────
def test_structured_same_trip_is_proof():
    # Same trip id → near-certain, scores 1.0 even with different seats.
    assert structured_match_score("TRIP1", "TRIP1", "BUS1", "BUS9", 4, 40) == 1.0


def test_structured_same_bus_is_strong():
    # Same bus but no trip agreement → strong but not proof.
    assert structured_match_score(None, None, "BUS1", "BUS1", None, None) == 0.6


def test_structured_seat_proximity_bonus():
    # Same bus + adjacent seat (|5-6|<=2) → 0.6 + 0.15.
    assert structured_match_score(None, None, "BUS1", "BUS1", 5, 6) == 0.75


def test_structured_seat_alone_cannot_match():
    # No trip and no bus agreement → seat numbers alone score nothing.
    assert structured_match_score(None, None, "BUS1", "BUS2", 5, 5) == 0.0


def test_structured_parses_alphanumeric_seat():
    # 'A5' and 5 are within 2 seats → bonus applies on a same-trip hit (capped 1.0).
    assert structured_match_score("T", "T", None, None, "A5", 5) == 1.0


def test_unified_includes_structured_key():
    score = UnifiedScorer.compute(0.1, 0.0, 1.0, ocr_score=0.0, structured_score=0.6)
    assert "structured" in score
    assert score["structured"] == 0.6


def test_exact_trip_match_clears_threshold_alone():
    # A same-trip structured hit should surface a match even with no text/image.
    structured = structured_match_score("TRIP1", "TRIP1", None, None, None, None)
    score = UnifiedScorer.compute(0.0, 0.0, 1.0, ocr_score=0.0, structured_score=structured)
    assert score["is_match"] is True
    assert score["final"] == 1.0


def run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  PASS  {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} scorer tests passed.")


if __name__ == "__main__":
    run()
