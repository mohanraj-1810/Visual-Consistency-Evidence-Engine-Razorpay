# 🎤 Demo Script — Visual Consistency & Evidence Engine
## Razorpay Buildathon · Track 02: AI Risk Manager
### Duration: 3–5 minutes

---

## 00:00–00:30 — Problem Statement

**[Speak to the audience]**

> "Every payment gateway has KYC and transaction monitoring — but none of them look at what a merchant *actually shows* on their storefront.

> A counterfeit luxury goods seller uses the same text-based onboarding flow as a legitimate artisan.
> The only difference is *visual* — plagiarized catalog photos, distorted brand logos, and forged registration certificates.

> Today we're showing a system that adds an *explainable visual evidence layer* to merchant onboarding — without replacing any existing risk infrastructure."

---

## 00:30–01:00 — Solution Overview

**[Point to the UI]**

> "This is the Visual Consistency & Evidence Engine.

> It crawls a merchant's storefront, extracts product and brand visuals, runs them through a Vision Transformer, verifies against web evidence, and outputs an explainable 5-tier risk recommendation.

> Crucially: it never automatically rejects a merchant. It generates evidence for human risk analysts to act on."

**[Point to the banner at the top]**

> "Decision-support system for human analysts. Non-blocking. Always explainable."

---

## 01:00–02:00 — Demo Scenario 1: Clean Merchant (Low Risk)

**[Click "Run Scenario" on the Clean Merchant card]**

> "Our first scenario is Terracotta Heritage Studio — a legitimate handcrafted ceramics business.

> The system crawls their storefront, runs ViT cosine similarity across their product catalog against a web search index, checks their logo against registered brand archives, and performs forensic ELA integrity analysis on their registration certificate."

**[Wait for result — Score: ~5.0, Status: CLEAR]**

> "Result: Score 5 — Auto-Approve. No external visual matches. No logo inconsistency. No forensic anomalies.

> Now look at the 'WHY THIS DECISION?' panel. Zero severe signals. The corroboration gate found nothing to escalate.

> Compare this to what a naive dHash matcher would do — it flagged 5 of our 6 clean merchants as suspicious. This system flagged zero."

---

## 02:00–03:00 — Demo Scenario 2: Supplier / Ambiguous Case

**[Click "Run Scenario" on the Supplier card]**

> "Scenario 2 is Urban Velocity Footwear — a footwear reseller using authorized supplier catalog photography.

> Their product images are genuinely identical to official brand supplier catalogs. A naive image similarity tool would immediately flag this as HIGH risk."

**[Wait for result — Score: ~31.5, Status: LOW]**

> "Score 31. Standard Onboarding — not escalated.

> Here's why this matters: look at the evidence source classification in the WHY panel. The match is identified as *supplier catalog reuse* — a completely normal e-commerce business model for distributors and authorized resellers.

> The system doesn't ask: 'Is this image similar?' It asks: 'What does this similarity *mean* in merchant risk context?'

> This is the key differentiator."

---

## 03:00–04:00 — Demo Scenario 3: Corroborated Risk

**[Click "Run Scenario" on the Corroborated Risk card]**

> "Scenario 3 is Luxe Atelier Outlet — claiming to be an official flagship for a luxury designer brand.

> Their product image is a 99.8% ViT cosine match to the reference luxury handbag. And their brand logo shows 62.9% divergence from the verified trademark."

**[Wait for result — Score: 55.0, Status: MEDIUM]**

> "Score 55. Enhanced Verification triggered.

> Look at the WHY panel — two signals detected: strong image similarity *and* logo trademark divergence exceeding 60%. One severe signal isn't enough to escalate to HIGH. Two independent signals triggered the verification queue.

> The analyst is shown exactly *what* to verify: request brand authorization letter, verify trademark ownership.

> No black box. No automatic rejection. Evidence → Confidence → Corroboration → Decision."

---

## 04:00–05:00 — Explainability + Business Impact

**[Scroll to show the Visual Merchant Profile and Why Decision panels]**

> "Every decision comes with three things judges care about:

> **1. Evidence** — what was actually detected, with exact similarity scores.
> **2. Corroboration** — was it independently verified or a single noisy match?
> **3. Recommended Actions** — what should the analyst do next?

> For Razorpay specifically: this system doesn't replace KYC or transaction monitoring.
> It adds one thing those systems completely miss: *visual evidence*.

> A merchant who copy-pastes 20 brand catalog images and submits a spliced certificate will pass every text-based risk screen. This system is the only layer that catches it — and it does so without generating a wave of false alarms on 50,000 legitimate dropshippers.

> That's the value: not just detection — *bounded, explainable, gated detection* at onboarding scale."

**[Show evaluation benchmark table from README]**

> "We evaluated across 23 held-out merchant archetypes. The full system achieves 0% false alarms on clean merchants. Naive ViT-only produced 16.7% false alarms. dHash produced 83%.

> The lower aggregate accuracy is by design — the corroboration gate intentionally refuses to escalate uncorroborated single matches. That's not a bug. That's the product."

---

## Key Talking Points for Questions

- **"Why not just use image similarity?"** — Because 100% of dropshippers look suspicious to a naive matcher. You need context.
- **"Is this production-ready?"** — This is a proof-of-concept that demonstrates the evidence pattern. Production deployment needs load testing, larger datasets, and integration with Razorpay's existing risk stack.
- **"What about live web search?"** — The demo uses deterministic offline fixtures. In production, live Serper.dev / DuckDuckGo evidence discovery runs in real-time.
- **"What's the False Positive Rate?"** — 0% on 6 clean benchmark cases. Not generalizable to production scale, but demonstrates the principle.
