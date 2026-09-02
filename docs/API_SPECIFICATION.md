# Visual Consistency Evidence Engine — REST API Specification

This document details all REST endpoints provided by the FastAPI backend server.

---

## Base URL
```
http://localhost:8000
```

---

## Endpoints

### 1. Health & Readiness Check
Check the API server status.

- **URL:** `/health`
- **Method:** `GET`
- **Response:** `200 OK`
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### 2. Merchant Storefront Verification
Initiates full visual consistency analysis for a given merchant domain or image batch.

- **URL:** `/api/verify`
- **Method:** `POST`
- **Request Headers:**
  - `Content-Type: application/json`
- **Request Body:**
```json
{
  "website_url": "https://sample-merchant.com",
  "merchant_name": "Acme Retail",
  "category": "apparel",
  "claimed_brand": "Acme",
  "claims": {
    "inventory_claim": "Proprietary designed luxury apparel",
    "brand_claim": "Registered domestic apparel trademark",
    "compliance_claim": "Authorized reseller"
  }
}
```

- **Response Body (`200 OK`):**
```json
{
  "status": "COMPLETED",
  "merchant_url": "https://sample-merchant.com",
  "visual_risk_score": 15,
  "risk_level": "LOW",
  "recommended_action": "NORMAL_FLOW",
  "brand_verification_status": "VERIFIED",
  "evidence_items": [
    {
      "evidence_type": "image_reuse",
      "title": "Product Visual Reuse",
      "score": 12.0,
      "similarity_pct": 12,
      "severity": "LOW",
      "relationship": "SUPPORTS",
      "source_type": "ONLINE",
      "source_domain": "sample-merchant.com",
      "explanation": "No significant visual reuse detected. Product images appear original."
    }
  ],
  "reasoning_summary": {
    "conclusion": "Storefront demonstrates high visual consistency across product catalog and brand assets.",
    "recommendation": "Proceed with automated onboarding."
  }
}
```

---

### 3. List Evaluation Test Cases
Retrieves the list of curated demo and borderline evaluation cases.

- **URL:** `/api/eval/cases`
- **Method:** `GET`
- **Response (`200 OK`):**
```json
[
  {
    "id": "legit_01_artisanal_ceramics",
    "title": "Artisanal Ceramics",
    "category": "Home Decor",
    "risk_expectation": "LOW"
  },
  {
    "id": "bord_01_urban_distributor",
    "title": "Urban Distributor",
    "category": "Apparel",
    "risk_expectation": "REVIEW"
  }
]
```

---

### 4. Execute Evaluation Case
Runs automated verification against a specific fixture case.

- **URL:** `/api/eval/run`
- **Method:** `POST`
- **Request Body:**
```json
{
  "case_id": "legit_01_artisanal_ceramics"
}
```
