"""
backend/evaluation/evaluate_pipeline.py — AI Risk Manager Pipeline Evaluation Suite.
Measures empirical precision, recall, F1, confusion matrix, and false-positive cost
on a held-out test suite across Clean (LOW), Borderline (MEDIUM), and Suspicious (HIGH) merchant cases.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
from PIL import Image
import numpy as np

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure utf-8 output for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from visual.vit_embeddings import load_vit_model
from routes.analyze import run_pipeline, DATASET_DIR
from sklearn.metrics import classification_report, confusion_matrix


def load_all_eval_cases(dataset_dir: Path) -> List[Dict[str, Any]]:
    """
    Scans the held-out evaluation dataset (eval_set/clean, eval_set/suspicious, eval_set/borderline)
    and loads each merchant case into standardized pipeline input.
    """
    eval_root = dataset_dir / "eval_set"
    if not eval_root.exists():
        # Fallback to backend/dataset/eval_set if relative
        eval_root = BACKEND_DIR / "dataset" / "eval_set"

    if not eval_root.exists():
        raise FileNotFoundError(f"Evaluation directory not found at {eval_root}. Run generate_demo_dataset.py first.")

    cases = []

    categories = [
        ("clean", "LOW"),
        ("borderline", "MEDIUM"),
        ("suspicious", "HIGH"),
    ]

    for folder_name, ground_truth in categories:
        category_dir = eval_root / folder_name
        if not category_dir.exists():
            continue

        for case_dir in sorted(category_dir.iterdir()):
            if not case_dir.is_dir():
                continue

            # Load metadata
            meta_path = case_dir / "meta.json"
            meta = {}
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

            # Load product images
            product_images = []
            for p_file in sorted(case_dir.glob("product_*.jpg")):
                try:
                    product_images.append(Image.open(p_file).convert("RGB"))
                except Exception:
                    pass

            # Load logo
            logo_path = case_dir / "logo.png"
            logo_image = Image.open(logo_path).convert("RGB") if logo_path.exists() else None

            # Load document
            doc_path = case_dir / "document.jpg"
            doc_image = Image.open(doc_path).convert("RGB") if doc_path.exists() else None

            cases.append({
                "case_id": case_dir.name,
                "folder_category": folder_name,
                "ground_truth": ground_truth,
                "merchant_name": meta.get("name", case_dir.name),
                "claimed_brand": meta.get("claimed_brand"),
                "product_images": product_images,
                "logo_image": logo_image,
                "document_image": doc_image,
                "claims": meta.get("claims", {
                    "inventory_claim": "Self-reported product ownership.",
                    "brand_claim": "Claimed brand identity.",
                    "compliance_claim": "Statutory registration disclosure.",
                }),
                "crawler_data": meta.get("crawler_data"),
            })

    return cases


def evaluate_pipeline():
    """
    Executes the multimodal risk pipeline over the held-out evaluation dataset,
    computes honest classification metrics and false-positive cost analysis,
    and writes the results to backend/evaluation/results.json.
    """
    print("=" * 80)
    print("AI RISK MANAGER (TRACK 02) — HELD-OUT TEST SET EVALUATION")
    print("=" * 80)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Dataset root: {DATASET_DIR / 'eval_set'}\n")

    # 1. Warm model
    print("[1/4] Warming Vision Transformer model backbone...")
    load_vit_model()

    # 2. Load held-out test cases
    print("[2/4] Loading held-out merchant cases from eval_set/...")
    cases = load_all_eval_cases(DATASET_DIR)
    print(f"  Loaded {len(cases)} held-out merchant cases across 3 risk tiers.\n")

    # 3. Run pipeline on every merchant case
    print("[3/4] Running multimodal inference across all test cases...")
    y_true = []
    y_pred = []
    case_results = []

    for idx, c in enumerate(cases, 1):
        start_t = time.time()
        res = run_pipeline(
            merchant_name=c["merchant_name"],
            product_images=c["product_images"],
            logo_image=c["logo_image"],
            document_image=c["document_image"],
            claimed_brand=c["claimed_brand"],
            claims=c["claims"],
            crawler_data=c["crawler_data"],
        )
        elapsed_ms = (time.time() - start_t) * 1000

        pred_status = res["fusion"]["status"]  # LOW, MEDIUM, or HIGH
        gt_status = c["ground_truth"]          # LOW, MEDIUM, or HIGH

        y_true.append(gt_status)
        y_pred.append(pred_status)

        match = (pred_status == gt_status)
        case_results.append({
            "case_id": c["case_id"],
            "merchant_name": c["merchant_name"],
            "category": c["folder_category"],
            "ground_truth": gt_status,
            "predicted_status": pred_status,
            "final_risk_score": res["fusion"]["final_risk_score"],
            "text_risk_score": res["fusion"]["text_risk_score"],
            "visual_risk_score": res["fusion"]["visual_risk_score"],
            "correct": match,
            "latency_ms": round(elapsed_ms, 2),
        })

        icon = "[MATCH]" if match else "[DIFF]"
        print(f"  [{idx:02d}/{len(cases):02d}] {icon} {c['case_id']:32} | GT: {gt_status:6} -> PRED: {pred_status:6} (Score: {res['fusion']['final_risk_score']:4.1f})")

    # 4. Compute Metrics
    print("\n" + "=" * 80)
    print("[4/4] COMPUTING METRICS & FALSE-POSITIVE COST")
    print("=" * 80)

    labels = ["LOW", "MEDIUM", "HIGH"]
    
    # Classification Report
    clf_report_dict = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)
    clf_report_text = classification_report(y_true, y_pred, labels=labels, zero_division=0)

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # False-Positive Cost Breakdown (Clean merchants flagged as MEDIUM or HIGH)
    clean_cases = [r for r in case_results if r["ground_truth"] == "LOW"]
    total_clean = len(clean_cases)
    clean_fps = [r for r in clean_cases if r["predicted_status"] in ["MEDIUM", "HIGH"]]
    fp_count = len(clean_fps)
    fp_rate = (fp_count / total_clean) if total_clean > 0 else 0.0

    # False-Negative Cost Breakdown (Suspicious merchants flagged as LOW)
    susp_cases = [r for r in case_results if r["ground_truth"] == "HIGH"]
    total_susp = len(susp_cases)
    susp_fns = [r for r in susp_cases if r["predicted_status"] == "LOW"]
    fn_count = len(susp_fns)
    fn_rate = (fn_count / total_susp) if total_susp > 0 else 0.0

    # Overall Accuracy
    total_cases = len(cases)
    correct_cases = sum(1 for r in case_results if r["correct"])
    accuracy = correct_cases / total_cases if total_cases > 0 else 0.0

    # Print Formatted Report
    print("\nPER-CLASS CLASSIFICATION REPORT:")
    print("-" * 65)
    print(clf_report_text)
    print("-" * 65)

    print("\nCONFUSION MATRIX (Rows: Ground Truth, Cols: Predicted):")
    print(f"{'':15} | {'PRED: LOW':>10} | {'PRED: MED':>10} | {'PRED: HIGH':>10}")
    print("-" * 55)
    for i, label in enumerate(labels):
        print(f"ACTUAL: {label:7} | {cm[i][0]:>10} | {cm[i][1]:>10} | {cm[i][2]:>10}")
    print("-" * 55)

    print("\nBUSINESS RISK & COST METRICS:")
    print("=" * 65)
    print(f"• Total Evaluation Cases:           {total_cases}")
    print(f"• Exact Tier Accuracy:              {accuracy * 100:.1f}% ({correct_cases}/{total_cases})")
    print(f"• Macro F1-Score:                   {clf_report_dict['macro avg']['f1-score']:.3f}")
    print(f"• Weighted F1-Score:                {clf_report_dict['weighted avg']['f1-score']:.3f}")
    print()
    print(f"• FALSE-POSITIVE COST (Clean Merchants Delayed by Review):")
    print(f"  - Count:                          {fp_count} / {total_clean} clean merchants")
    print(f"  - False-Positive Rate (FPR):      {fp_rate * 100:.1f}%")
    print(f"  - Business Impact:                Legitimate merchants delayed by human review queue.")
    print()
    print(f"• FALSE-NEGATIVE COST (Fraudulent Merchants Approved):")
    print(f"  - Count:                          {fn_count} / {total_susp} suspicious merchants")
    print(f"  - False-Negative Rate (FNR):      {fn_rate * 100:.1f}%")
    print(f"  - Business Impact:                Fraudulent merchants bypassing onboarding filters.")
    print("=" * 65)

    # Save to results.json
    output_path = BACKEND_DIR / "evaluation" / "results.json"
    results_payload = {
        "evaluation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_path": str(DATASET_DIR / "eval_set"),
        "total_cases": total_cases,
        "overall_accuracy": round(accuracy, 4),
        "macro_f1": round(clf_report_dict["macro avg"]["f1-score"], 4),
        "weighted_f1": round(clf_report_dict["weighted avg"]["f1-score"], 4),
        "per_class_metrics": {
            "LOW": clf_report_dict.get("LOW", {}),
            "MEDIUM": clf_report_dict.get("MEDIUM", {}),
            "HIGH": clf_report_dict.get("HIGH", {}),
        },
        "confusion_matrix": {
            "labels": labels,
            "matrix": cm.tolist(),
        },
        "false_positive_analysis": {
            "metric_name": "False Positive Rate on Clean Merchants",
            "clean_total": total_clean,
            "clean_flagged_medium_or_high": fp_count,
            "false_positive_rate": round(fp_rate, 4),
            "business_cost_explanation": "Operational cost: Legitimate clean merchants delayed by unnecessary manual analyst review.",
        },
        "false_negative_analysis": {
            "metric_name": "False Negative Rate on Suspicious Merchants",
            "suspicious_total": total_susp,
            "suspicious_flagged_low": fn_count,
            "false_negative_rate": round(fn_rate, 4),
            "business_cost_explanation": "Financial / Risk cost: High-risk deceptive merchants incorrectly auto-approved.",
        },
        "individual_case_results": case_results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\nEvaluation results successfully saved to: {output_path}")
    return results_payload


if __name__ == "__main__":
    evaluate_pipeline()
