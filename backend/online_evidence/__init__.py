"""
backend/online_evidence — Online Visual Evidence Discovery & Reasoning Engine.
Discovers candidate public web visuals, verifies similarity using ViT, and maps
findings into structured Claim vs. Visual Evidence reasoning objects.
"""

from .provider import BaseEvidenceProvider, WebSearchEvidenceProvider, LocalReferenceEvidenceProvider
from .candidate_search import discover_candidate_evidence
from .verifier import verify_candidates_with_vit, CandidateMatch
from .reasoning import (
    EvidenceObject,
    generate_structured_evidence,
    synthesize_claims_reasoning,
    get_analysis_provenance,
)

__all__ = [
    "BaseEvidenceProvider",
    "WebSearchEvidenceProvider",
    "LocalReferenceEvidenceProvider",
    "discover_candidate_evidence",
    "verify_candidates_with_vit",
    "CandidateMatch",
    "EvidenceObject",
    "generate_structured_evidence",
    "synthesize_claims_reasoning",
    "get_analysis_provenance",
]
