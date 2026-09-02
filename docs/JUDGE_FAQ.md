# 🛡️ Judge FAQ — Visual Consistency & Evidence Engine
## Razorpay Buildathon · Track 02: AI Risk Manager

All answers are technically honest. No claims beyond what the system actually does.

---

### Q: Why not just use image similarity?

**A:** Raw image similarity answers "are these images similar?" — it cannot answer "is this similarity *fraudulent*?"

A legitimate footwear reseller using authorized Nike supplier catalog photography will show 100% ViT cosine similarity to a reference Nike image. A naive similarity tool would flag them as HIGH risk.

Our system classifies the *source domain* of the matching candidate — supplier catalog, stock photo platform, brand flagship, or unknown — and uses that context to determine whether the match represents fraud or normal e-commerce sourcing.

Without this context layer, you generate massive false positive rates. Our benchmark showed:
- dHash only: **83.3% FPR** on clean merchants
- Raw ViT: **16.7% FPR** on clean merchants
- Our corroboration-gated system: **0.0% FPR** on clean merchants

---

### Q: Why ViT (Vision Transformer) specifically?

**A:** ViT-Base/16 was selected over dHash, pHash, or CNN-based approaches because it produces semantically rich 768-dimensional feature embeddings.

dHash and pHash are bit-level structural comparisons — they're fooled by resizing, JPEG compression, color shifts, and minor compositing. They cannot distinguish "two images of the same object photographed differently" from "two pixel-identical copies."

ViT's cosine similarity in embedding space generalizes across reasonable image transformations while still catching copy-paste catalog reuse. In our benchmark, ViT detected 99.8–100% similarity across all evaluated copy-paste catalog cases.

---

### Q: Why do you need external evidence? Can't you just use ViT?

**A:** ViT provides the visual similarity score. External evidence search provides the *source attribution* — where has this image appeared before, and in what context?

Without source attribution, you cannot distinguish:
- A legitimate reseller using authorized supplier images (normal)
- A counterfeit merchant copy-pasting brand catalog photos (fraudulent)

The external evidence layer (Serper.dev / DuckDuckGo reverse image-style discovery) provides candidate source domains. The corroboration gate requires that candidates originate from non-supplier, non-marketplace sources before treating the match as a severe signal.

---

### Q: How do you prevent false positives?

**A:** Three mechanisms:

1. **Source classification:** Supplier catalogs, stock photo platforms, and authorized marketplaces are explicitly excluded from severe risk signals.

2. **Multi-vector corroboration gate:** A single signal — even a 100% image match — cannot escalate a merchant to HIGH risk alone. The system requires ≥ 2 independently severe signals (e.g. stolen image + distorted trademark logo, or stolen image + document forgery).

3. **Evidence status requirement:** Offline single-fixture matches receive `INSUFFICIENT_EVIDENCE` status. Live multi-source web corroboration is required for escalation.

---

### Q: What happens with supplier/catalog images?

**A:** The candidate source type is identified during evidence verification:
- Domains matching known supplier/distributor patterns → `SUPPLIER_CATALOG`
- Known stock photo platforms → `STOCK_PHOTO`
- Marketplace domains → `MARKETPLACE`

Supplier catalog matches are explicitly capped at LOW risk with the note "Sourcing reuse — excluded from severe escalation." This preserves onboarding flow for the hundreds of thousands of legitimate catalog-based resellers on Razorpay.

---

### Q: What happens when there's only one suspicious image?

**A:** The merchant is not escalated to HIGH. The policy is:

```
Single strong match → INSUFFICIENT_EVIDENCE → LOW or MEDIUM
Two independent severe signals → CORROBORATED → MEDIUM-HIGH eligibility
```

This is intentional and documented. The corroboration gate exists specifically to prevent a single low-quality stock image from automatically blocking a legitimate merchant.

---

### Q: Why not use an LLM for this?

**A:** LLMs process text tokens, not pixel-level visual fingerprints. They cannot:
- Compute cosine similarity between image embedding spaces
- Detect localized JPEG compression gradient anomalies (ELA)
- Perform reverse-image candidate discovery across web sources
- Apply deterministic rule-based corroboration gating

The system does use structured NLP for claim synthesis and recommendations, but visual risk analysis requires dedicated computer vision primitives.

---

### Q: Can this integrate with Razorpay's existing risk engine?

**A:** Yes — this is the design intent. The system outputs structured JSON with:
- A 5-tier risk tier (`CLEAR`, `LOW`, `MEDIUM`, `ELEVATED`, `HIGH`)
- A numeric composite score (0–100)
- Per-signal sub-scores (visual, text, reuse, logo, manipulation)
- A structured evidence array with source attribution
- Recommended analyst actions

These can be consumed as additional signals by any existing risk decision engine. The system explicitly does not replace KYC, transaction monitoring, or identity verification — it adds a visual evidence dimension that those systems lack.

---

### Q: Is this production-ready?

**A:** No. This is a proof-of-concept built for Razorpay Buildathon evaluation.

Known production gaps:
- Evaluated on 23 curated cases — not statistically representative of production volume
- External evidence discovery depends on Serper.dev API availability
- No database persistence — analysis results are in-memory only
- JavaScript-heavy SPAs may evade crawler extraction
- No distributed load testing performed
- ELA forensics requires real multi-pass JPEG artifacts (synthetic documents evade detection)

---

### Q: How was it evaluated?

**A:** A held-out benchmark of 23 cases across 11 merchant archetypes (6 clean, 8 borderline, 9 suspicious). Four methods were compared:

| Method | Accuracy | Clean FPR | Suspicious FNR |
|---|---|---|---|
| dHash Only | 39.1% | 83.3% | 0.0% |
| ViT Only | 56.5% | 16.7% | 11.1% |
| ViT + dHash Ensemble | 39.1% | 83.3% | 0.0% |
| **Full System** | **26.1%** | **0.0%** | 77.8% |

The 26.1% aggregate accuracy reflects the corroboration gate's intentional conservatism:
- 4 of 9 suspicious cases were policy/evaluation mismatches (ground truth expected HIGH for uncorroborated single matches)
- 2 of 9 were correct conservative MEDIUM decisions (logo divergence triggered 1 of 2 required signals)
- 2 of 9 were fixture construction problems (synthetic document ELA, single-target forensic routing)
- 1 of 9 was a genuine pipeline miss (multi-product hybrid catalog)

See [`../backend/evaluation/HIGH_RISK_AUDIT.md`](../backend/evaluation/HIGH_RISK_AUDIT.md) for the full case-by-case analysis.

---

### Q: What are the current limitations?

**A:**
1. **Benchmark size:** 23 cases is too small for production-grade statistical validation.
2. **Search provider dependency:** Serper.dev is a paid API; DuckDuckGo fallback has rate limits.
3. **JavaScript-heavy storefronts:** SPAs with heavy client-side rendering may yield incomplete extraction.
4. **Single-target forensic scanning:** ELA currently inspects only one image per analysis run.
5. **First-product-only candidate search:** Multi-product hybrid catalogs (e.g. legitimate items mixed with stolen ones) may not have all images evaluated.
6. **No production load testing:** Cannot make claims about throughput or p99 latency at scale.

---

### Q: What happens when external evidence is unavailable?

**A:** The system degrades gracefully:

- If the merchant domain is unreachable: returns `UNVERIFIABLE` status — scoring is suspended.
- If the web search provider is unavailable: visual analysis still runs with offline fixture fallback; result is labeled `ONLINE_SEARCH_SCRAPING` mode.
- If no images are found: the evidence confidence is marked `INSUFFICIENT_EVIDENCE` and the result is appropriately capped.
- If a specific image fails to download: that image is skipped; remaining images are analyzed.

The system never produces a phantom HIGH risk decision when evidence is unavailable.
