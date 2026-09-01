"""
generate_demo_dataset.py — High-Fidelity Controlled Demo & Evaluation Dataset Generator.
Creates authentic visual assets for reference catalogs, verified brand marks,
live demo cases (dataset/merchants/), and a held-out evaluation test suite (dataset/eval_set/).
Ensures all risk scores are derived dynamically from real visual analysis algorithms.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import numpy as np
import cv2

# Ensure UTF-8 output across Windows, Linux and macOS
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass



def draw_realistic_watch(size=(450, 450), color_scheme="luxury") -> Image.Image:
    """Generate a high-detail luxury chronograph timepiece."""
    img = Image.new("RGB", size, (15, 23, 42))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Background subtle radial vignette
    for r in range(size[0] // 2, 0, -10):
        val = int(15 + (1.0 - r / (size[0] / 2)) * 25)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(val, val + 5, val + 15))

    # Leather Strap
    strap_col = (45, 25, 18) if color_scheme == "luxury" else (20, 20, 25)
    draw.rectangle([cx - 45, 10, cx + 45, cy - 130], fill=strap_col, outline=(30, 15, 10), width=3)
    draw.rectangle([cx - 45, cy + 130, cx + 45, size[1] - 10], fill=strap_col, outline=(30, 15, 10), width=3)
    # Strap stitching
    for y in range(20, cy - 135, 12):
        draw.line([cx - 40, y, cx - 40, y + 6], fill=(180, 150, 100), width=2)
        draw.line([cx + 40, y, cx + 40, y + 6], fill=(180, 150, 100), width=2)
    for y in range(cy + 140, size[1] - 20, 12):
        draw.line([cx - 40, y, cx - 40, y + 6], fill=(180, 150, 100), width=2)
        draw.line([cx + 40, y, cx + 40, y + 6], fill=(180, 150, 100), width=2)

    # Steel/Gold Case
    bezel_col = (212, 175, 55) if color_scheme == "luxury" else (190, 195, 205)
    draw.ellipse([cx - 135, cy - 135, cx + 135, cy + 135], fill=(30, 30, 35), outline=bezel_col, width=10)
    draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=(20, 24, 32), outline=(80, 85, 95), width=3)

    # Dial Hour Markers & Ticks
    for angle in range(0, 360, 30):
        rad = np.deg2rad(angle)
        x1 = cx + int(95 * np.cos(rad))
        y1 = cy + int(95 * np.sin(rad))
        x2 = cx + int(112 * np.cos(rad))
        y2 = cy + int(112 * np.sin(rad))
        draw.line([x1, y1, x2, y2], fill=bezel_col, width=4 if angle % 90 == 0 else 2)

    # Sub-dials (Chronograph)
    draw.ellipse([cx - 45, cy - 15, cx - 15, cy + 15], outline=(100, 110, 125), width=2)
    draw.ellipse([cx + 15, cy - 15, cx + 45, cy + 15], outline=(100, 110, 125), width=2)
    draw.ellipse([cx - 15, cy + 30, cx + 15, cy + 60], outline=(100, 110, 125), width=2)

    # Dial Brand Text
    draw.text((cx - 38, cy - 65), "CHRONOMASTER", fill=(230, 230, 235))
    draw.text((cx - 28, cy - 50), "AUTOMATIC", fill=(160, 165, 175))

    # Hands
    draw.line([cx, cy, cx + 55, cy - 45], fill=bezel_col, width=5)
    draw.line([cx, cy, cx - 35, cy - 65], fill=(240, 240, 245), width=4)
    draw.line([cx, cy, cx + 40, cy + 50], fill=(220, 40, 40), width=2)
    draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=bezel_col, outline=(20, 20, 20), width=2)

    # Glass highlight glare
    draw.arc([cx - 110, cy - 110, cx + 110, cy + 110], start=210, end=320, fill=(255, 255, 255), width=3)
    return img


def draw_realistic_handbag(size=(450, 450), leather_color=(120, 65, 35)) -> Image.Image:
    """Generate a high-detail luxury Italian leather designer handbag."""
    img = Image.new("RGB", size, (28, 25, 30))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Bag body trapezoid
    pts = [
        (cx - 140, cy + 120),
        (cx + 140, cy + 120),
        (cx + 105, cy - 45),
        (cx - 105, cy - 45),
    ]
    draw.polygon(pts, fill=leather_color, outline=(40, 20, 10), width=5)

    # Textured grain overlay
    for y in range(cy - 40, cy + 115, 16):
        draw.line([cx - 95, y, cx + 95, y], fill=(leather_color[0] + 15, leather_color[1] + 10, leather_color[2] + 5), width=2)

    # Flap
    flap_pts = [
        (cx - 105, cy - 45),
        (cx + 105, cy - 45),
        (cx + 70, cy + 45),
        (cx - 70, cy + 45),
    ]
    draw.polygon(flap_pts, fill=(leather_color[0] - 15, leather_color[1] - 10, leather_color[2] - 5), outline=(212, 175, 55), width=3)

    # Gold Clasp / Lock
    draw.rectangle([cx - 24, cy + 30, cx + 24, cy + 62], fill=(212, 175, 55), outline=(170, 130, 25), width=2)
    draw.ellipse([cx - 6, cy + 40, cx + 6, cy + 52], fill=(40, 30, 10))

    # Handles
    draw.arc([cx - 75, cy - 135, cx + 75, cy - 25], start=180, end=0, fill=(45, 25, 15), width=10)
    draw.arc([cx - 75, cy - 135, cx + 75, cy - 25], start=180, end=0, fill=(212, 175, 55), width=2)

    return img


def draw_realistic_sneaker(size=(450, 450), primary_color=(25, 100, 230)) -> Image.Image:
    """Generate an athletic performance sneaker asset."""
    img = Image.new("RGB", size, (20, 24, 33))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Sole
    draw.rounded_rectangle([cx - 150, cy + 60, cx + 150, cy + 105], radius=16, fill=(245, 245, 250), outline=(180, 185, 195), width=4)
    # Air cushion bubble
    draw.rounded_rectangle([cx - 70, cy + 68, cx + 20, cy + 96], radius=8, fill=(0, 210, 255), outline=(0, 160, 200), width=2)

    # Upper Body
    body_pts = [
        (cx - 140, cy + 60),
        (cx - 90, cy - 25),
        (cx - 10, cy - 50),
        (cx + 45, cy - 10),
        (cx + 140, cy + 35),
        (cx + 140, cy + 60),
    ]
    draw.polygon(body_pts, fill=primary_color, outline=(20, 20, 30), width=4)

    # Dynamic Swoosh Stripe
    draw.line([cx - 85, cy + 25, cx + 15, cy + 40, cx + 110, cy + 10], fill=(255, 255, 255), width=9)
    # Laces
    for lx in range(cx - 70, cx + 25, 18):
        draw.line([lx, cy - 5, lx + 12, cy - 25], fill=(235, 235, 240), width=4)

    return img


def draw_realistic_headphones(size=(450, 450), accent_color=(0, 160, 255)) -> Image.Image:
    """Generate high-fidelity wireless studio headphones."""
    img = Image.new("RGB", size, (18, 20, 26))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Headband
    draw.arc([cx - 115, cy - 135, cx + 115, cy + 25], start=180, end=0, fill=(35, 40, 48), width=20)
    draw.arc([cx - 115, cy - 135, cx + 115, cy + 25], start=180, end=0, fill=accent_color, width=3)

    # Ear cups
    draw.ellipse([cx - 135, cy - 25, cx - 65, cy + 90], fill=(25, 28, 35), outline=accent_color, width=6)
    draw.ellipse([cx - 120, cy - 10, cx - 80, cy + 75], fill=(15, 16, 20))

    draw.ellipse([cx + 65, cy - 25, cx + 135, cy + 90], fill=(25, 28, 35), outline=accent_color, width=6)
    draw.ellipse([cx + 80, cy - 10, cx + 120, cy + 75], fill=(15, 16, 20))

    return img


def draw_artisanal_pottery(size=(450, 450), clay_color=(215, 135, 95)) -> Image.Image:
    """Generate an authentic handcrafted terracotta ceramic vessel for Clean merchant."""
    img = Image.new("RGB", size, (245, 240, 232))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Warm natural drop shadow
    draw.ellipse([cx - 100, cy + 95, cx + 100, cy + 125], fill=(215, 208, 195))

    # Rim
    draw.ellipse([cx - 85, cy - 90, cx + 85, cy - 55], fill=(clay_color[0] - 25, clay_color[1] - 20, clay_color[2] - 15), outline=(130, 65, 40), width=3)

    # Body curves
    body = [
        (cx - 85, cy - 72),
        (cx + 85, cy - 72),
        (cx + 120, cy + 25),
        (cx + 65, cy + 105),
        (cx - 65, cy + 105),
        (cx - 120, cy + 25),
    ]
    draw.polygon(body, fill=clay_color, outline=(130, 65, 40), width=4)
    draw.ellipse([cx - 65, cy + 90, cx + 65, cy + 120], fill=(clay_color[0] - 35, clay_color[1] - 30, clay_color[2] - 25))

    # Artisanal hand-painted glaze patterns
    for i in range(-50, 50, 20):
        draw.arc([cx - 60, cy + i - 10, cx + 60, cy + i + 10], start=0, end=180, fill=(240, 225, 200), width=3)

    return img


def draw_handwoven_textile(size=(450, 450), hue_offset=0) -> Image.Image:
    """Generate authentic organic linen scarf texture for Clean merchant."""
    img = Image.new("RGB", size, (242 + hue_offset, 238, 230 - hue_offset))
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2

    # Scarf folds
    poly = [(cx - 120, cy - 100), (cx + 100, cy - 80), (cx + 130, cy + 90), (cx - 90, cy + 115)]
    draw.polygon(poly, fill=(225, 220, 205), outline=(160, 150, 135), width=3)

    for y in range(-80, 95, 14):
        draw.line([cx - 105, cy + y, cx + 115, cy + y + 10], fill=(185, 175, 160), width=2)
    for x in range(-90, 95, 16):
        draw.line([cx + x, cy - 85, cx + x + 15, cy + 100], fill=(195, 185, 170), width=1)

    return img


def draw_official_logo(brand_name: str, symbol: str, bg=(15, 23, 42), fg=(212, 175, 55), size=(320, 320)) -> Image.Image:
    """Create a verified corporate/luxury brand logo."""
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    cx, cy = size[0] // 2, size[1] // 2 - 25

    if symbol == "diamond":
        draw.polygon([(cx, cy - 65), (cx + 65, cy), (cx, cy + 65), (cx - 65, cy)], fill=fg)
        draw.polygon([(cx, cy - 42), (cx + 42, cy), (cx, cy + 42), (cx - 42, cy)], fill=bg)
        draw.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=fg)
    elif symbol == "crest":
        draw.rounded_rectangle([cx - 60, cy - 60, cx + 60, cy + 60], radius=20, fill=fg)
        draw.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=bg)
        draw.polygon([(cx - 22, cy + 10), (cx, cy - 28), (cx + 22, cy + 10)], fill=fg)
    elif symbol == "distorted":
        draw.polygon([(cx - 15, cy - 75), (cx + 75, cy - 5), (cx + 5, cy + 70), (cx - 75, cy + 10)], fill=(220, 45, 45))
        draw.line([cx - 65, cy - 10, cx + 65, cy + 10], fill=(255, 230, 0), width=7)
    elif symbol == "artisanal":
        draw.ellipse([cx - 55, cy - 55, cx + 55, cy + 55], fill=fg)
        draw.ellipse([cx - 45, cy - 45, cx + 45, cy + 45], fill=bg)
        draw.text((cx - 15, cy - 15), "E&C", fill=fg)

    draw.text((cx - len(brand_name) * 4, size[1] - 52), brand_name.upper(), fill=fg)
    return img


def draw_official_certificate(is_tampered: bool = False, entity_name: str = "APEX GLOBAL LUXURY RETAIL LTD", size=(520, 680)) -> Image.Image:
    """Generate statutory incorporation certificate with optional forensic tampering."""
    img = Image.new("RGB", size, (252, 250, 244))
    draw = ImageDraw.Draw(img)

    # Gold/Bronze Certificate Borders
    draw.rectangle([18, 18, size[0] - 18, size[1] - 18], outline=(160, 130, 65), width=5)
    draw.rectangle([26, 26, size[0] - 26, size[1] - 26], outline=(210, 185, 120), width=2)

    # Header
    draw.text((size[0] // 2 - 130, 50), "CERTIFICATE OF INCORPORATION", fill=(25, 35, 55))
    draw.text((size[0] // 2 - 90, 75), "MINISTRY OF CORPORATE AFFAIRS", fill=(95, 100, 115))
    draw.line([60, 105, size[0] - 60, 105], fill=(180, 150, 80), width=2)

    # Document details
    y = 145
    lines = [
        "This is to certify that the business organization named herein",
        "has been duly incorporated pursuant to the Statutory Companies Act.",
        "",
        f"Entity Name:     {entity_name}",
        "Registration ID: CIN-U74999MH2021PTC368920",
        "Issue Date:      15 MARCH 2021",
        "Jurisdiction:    COMMERCIAL DIVISION",
        "Authorized Rep:  REGISTRAR GENERAL",
    ]
    for line in lines:
        draw.text((55, y), line, fill=(35, 40, 50))
        y += 28

    # Official Seal / Stamp
    draw.ellipse([size[0] - 175, size[1] - 185, size[0] - 55, size[1] - 65], outline=(175, 40, 40), width=4)
    draw.text((size[0] - 150, size[1] - 135), "OFFICIAL SEAL\n  VERIFIED", fill=(175, 40, 40))

    if not is_tampered:
        return img

    # Spliced forensic patches
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    patch1 = np.ones((38, 330, 3), dtype=np.uint8) * 255
    cv2.putText(patch1, "CIN-ALTERED-99482X", (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 160), 2)
    noise1 = np.random.normal(0, 22, patch1.shape).astype(np.int16)
    patch1_noisy = np.clip(patch1.astype(np.int16) + noise1, 0, 255).astype(np.uint8)
    cv_img[215:253, 145:475] = patch1_noisy

    patch2 = np.ones((32, 130, 3), dtype=np.uint8) * 248
    cv2.putText(patch2, "EXP: 2032", (6, 22), cv2.FONT_HERSHEY_DUPLEX, 0.6, (180, 15, 15), 2)
    noise2 = np.random.normal(0, 18, patch2.shape).astype(np.int16)
    patch2_noisy = np.clip(patch2.astype(np.int16) + noise2, 0, 255).astype(np.uint8)
    cv_img[size[1] - 125 : size[1] - 93, size[0] - 165 : size[0] - 35] = patch2_noisy

    _, enc = cv2.imencode(".jpg", cv_img, [int(cv2.IMWRITE_JPEG_QUALITY), 65])
    recompressed = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return Image.fromarray(cv2.cvtColor(recompressed, cv2.COLOR_BGR2RGB))


def build_all_demo_datasets():
    """Generate all controlled catalog references, logos, and live demo cases."""
    bases = [Path("dataset"), Path("backend/dataset")]

    for base_dir in bases:
        # 1. reference
        ref_dir = base_dir / "reference"
        ref_dir.mkdir(parents=True, exist_ok=True)

        ref_watch = draw_realistic_watch(color_scheme="luxury")
        ref_watch.save(ref_dir / "ref_luxury_watch_omega.jpg", quality=95)

        ref_bag = draw_realistic_handbag(leather_color=(125, 68, 38))
        ref_bag.save(ref_dir / "ref_handbag_leather.jpg", quality=95)

        ref_shoe = draw_realistic_sneaker(primary_color=(25, 100, 230))
        ref_shoe.save(ref_dir / "ref_sneaker_airmax.jpg", quality=95)

        ref_audio = draw_realistic_headphones()
        ref_audio.save(ref_dir / "ref_electronics_headphones.jpg", quality=95)

        # 2. logos
        logos_dir = base_dir / "logos"
        logos_dir.mkdir(parents=True, exist_ok=True)

        logo_apex = draw_official_logo("Apex Brands", "diamond", bg=(15, 23, 42), fg=(212, 175, 55))
        logo_apex.save(logos_dir / "verified_brand_apex.png")

        logo_luxe = draw_official_logo("Luxe Atelier", "crest", bg=(24, 24, 28), fg=(240, 240, 245))
        logo_luxe.save(logos_dir / "verified_brand_luxe.png")

        # 3. merchants/clean
        clean_dir = base_dir / "merchants" / "clean"
        clean_dir.mkdir(parents=True, exist_ok=True)

        clean_pot = draw_artisanal_pottery()
        clean_pot.save(clean_dir / "clean_product_1.jpg", quality=95)

        clean_textile = draw_handwoven_textile()
        clean_textile.save(clean_dir / "clean_product_2.jpg", quality=95)

        clean_logo = draw_official_logo("Earth & Clay", "artisanal", bg=(240, 236, 226), fg=(80, 55, 40))
        clean_logo.save(clean_dir / "clean_logo.png")

        clean_cert = draw_official_certificate(is_tampered=False, entity_name="EARTH & CLAY HANDCRAFTED STUDIO LTD")
        clean_cert.save(clean_dir / "clean_document.jpg", quality=95)

        # 4. merchants/suspicious
        suspicious_dir = base_dir / "merchants" / "suspicious"
        suspicious_dir.mkdir(parents=True, exist_ok=True)

        susp_watch = ref_watch.copy()
        susp_watch = ImageEnhance.Contrast(susp_watch).enhance(1.08)
        susp_watch = ImageEnhance.Brightness(susp_watch).enhance(0.97)
        susp_watch.save(suspicious_dir / "suspicious_product_1.jpg", quality=92)

        susp_bag = ref_bag.copy()
        susp_bag = ImageEnhance.Color(susp_bag).enhance(1.06)
        susp_bag.save(suspicious_dir / "suspicious_product_2.jpg", quality=90)

        susp_logo = draw_official_logo("Apex Brands", "distorted", bg=(255, 255, 255), fg=(220, 45, 45))
        susp_logo.save(suspicious_dir / "suspicious_logo.png")

        susp_doc = draw_official_certificate(is_tampered=True, entity_name="APEX GLOBAL LUXURY RETAIL LTD")
        susp_doc.save(suspicious_dir / "suspicious_tampered_doc.jpg", quality=88)

        # 5. merchants/borderline
        borderline_dir = base_dir / "merchants" / "borderline"
        borderline_dir.mkdir(parents=True, exist_ok=True)

        border_shoe = draw_realistic_sneaker(primary_color=(100, 115, 140))
        border_shoe.save(borderline_dir / "borderline_product_1.jpg", quality=90)

        border_logo = draw_official_logo("Apex Store", "crest", bg=(32, 35, 45), fg=(175, 180, 195))
        border_logo.save(borderline_dir / "borderline_logo.png")

        border_doc = draw_official_certificate(is_tampered=False, entity_name="URBAN VELOCITY SPORTS LTD")
        border_doc.save(borderline_dir / "borderline_document.jpg", quality=90)

    print("Demo dataset generated in dataset/ and backend/dataset/")


def build_held_out_evaluation_dataset():
    """
    Generate a genuinely held-out evaluation test suite (dataset/eval_set/)
    containing at least 6 distinct synthetic merchant cases per risk class
    (18 cases total) with varied visual parameters, tampering levels, and metadata.
    """
    bases = [Path("backend/dataset"), Path("dataset")]

    for base_dir in bases:
        eval_dir = base_dir / "eval_set"
        
        # ──────────────────────────────────────────────────────────
        # 1. CLEAN HELD-OUT TEST CASES (Ground Truth: LOW Risk)
        # ──────────────────────────────────────────────────────────
        clean_base = eval_dir / "clean"
        clean_base.mkdir(parents=True, exist_ok=True)

        clean_cases = [
            {
                "case_id": "clean_01_artisanal_terracotta",
                "name": "Terracotta Heritage Studio",
                "category": "Handmade Ceramics",
                "claimed_brand": "Terracotta Heritage",
                "img1": draw_artisanal_pottery(clay_color=(205, 120, 80)),
                "img2": draw_artisanal_pottery(clay_color=(215, 130, 90)),
                "logo": draw_official_logo("Terracotta Heritage", "artisanal", bg=(245, 240, 230), fg=(110, 60, 35)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="TERRACOTTA HERITAGE STUDIO PVT LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://ig.com/terracotta"]},
            },
            {
                "case_id": "clean_02_flora_linen",
                "name": "Flora Linen Weavers",
                "category": "Organic Textiles",
                "claimed_brand": "Flora Linen",
                "img1": draw_handwoven_textile(hue_offset=0),
                "img2": draw_handwoven_textile(hue_offset=4),
                "logo": draw_official_logo("Flora Linen", "artisanal", bg=(240, 245, 235), fg=(50, 90, 60)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="FLORA LINEN TEXTILES LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://fb.com/floralinen"]},
            },
            {
                "case_id": "clean_03_artisan_leathercraft",
                "name": "Heritage Hide Guild",
                "category": "Custom Leather Goods",
                "claimed_brand": "Heritage Hide",
                "img1": draw_realistic_handbag(leather_color=(75, 45, 25)),
                "img2": draw_realistic_handbag(leather_color=(80, 50, 30)),
                "logo": draw_official_logo("Heritage Hide", "artisanal", bg=(235, 230, 220), fg=(85, 45, 25)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="HERITAGE HIDE GUILD CO"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://ig.com/heritagehide"]},
            },
            {
                "case_id": "clean_04_aura_glassworks",
                "name": "Aura Handblown Glass",
                "category": "Studio Glassware",
                "claimed_brand": "Aura Glass",
                "img1": draw_artisanal_pottery(clay_color=(120, 180, 210)),
                "img2": draw_artisanal_pottery(clay_color=(100, 160, 190)),
                "logo": draw_official_logo("Aura Glass", "artisanal", bg=(240, 248, 255), fg=(30, 100, 140)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="AURA GLASSWORKS LLP"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://ig.com/auraglass"]},
            },
            {
                "case_id": "clean_05_timber_craft_studio",
                "name": "Timber Craft Studio",
                "category": "Artisan Woodworking",
                "claimed_brand": "Timber Craft",
                "img1": draw_artisanal_pottery(clay_color=(160, 110, 65)),
                "img2": draw_handwoven_textile(hue_offset=-3),
                "logo": draw_official_logo("Timber Craft", "artisanal", bg=(245, 235, 220), fg=(100, 60, 25)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="TIMBER CRAFT WOODWORKS PVT LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://timbercraft.io"]},
            },
            {
                "case_id": "clean_06_solstice_bespoke_gems",
                "name": "Solstice Gem Studio",
                "category": "Handmade Jewelry",
                "claimed_brand": "Solstice Gems",
                "img1": draw_artisanal_pottery(clay_color=(220, 170, 130)),
                "img2": draw_handwoven_textile(hue_offset=2),
                "logo": draw_official_logo("Solstice Gems", "artisanal", bg=(250, 245, 240), fg=(140, 90, 45)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="SOLSTICE GEMS & JEWELS LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://ig.com/solsticegems"]},
            },
        ]

        for c in clean_cases:
            cdir = clean_base / c["case_id"]
            cdir.mkdir(parents=True, exist_ok=True)
            c["img1"].save(cdir / "product_1.jpg", quality=95)
            c["img2"].save(cdir / "product_2.jpg", quality=95)
            c["logo"].save(cdir / "logo.png")
            c["doc"].save(cdir / "document.jpg", quality=95)
            meta = {
                "name": c["name"],
                "category": c["category"],
                "claimed_brand": c["claimed_brand"],
                "ground_truth": "LOW",
                "claims": {
                    "inventory_claim": f"Original handcrafted proprietary catalog by {c['name']}.",
                    "brand_claim": f"Registered artisanal trademark for {c['claimed_brand']}.",
                    "compliance_claim": "Statutory Certificate of Incorporation.",
                },
                "crawler_data": c["crawler"],
            }
            with open(cdir / "meta.json", "w") as f:
                json.dump(meta, f, indent=2)

        # ──────────────────────────────────────────────────────────
        # 2. SUSPICIOUS HELD-OUT TEST CASES (Ground Truth: HIGH Risk)
        # ──────────────────────────────────────────────────────────
        susp_base = eval_dir / "suspicious"
        susp_base.mkdir(parents=True, exist_ok=True)

        ref_watch = draw_realistic_watch(color_scheme="luxury")
        ref_bag = draw_realistic_handbag(leather_color=(125, 68, 38))
        ref_shoe = draw_realistic_sneaker(primary_color=(25, 100, 230))
        ref_audio = draw_realistic_headphones()

        susp_cases = [
            {
                "case_id": "susp_01_stolen_chronographs",
                "name": "Apex Chrono Flagship",
                "category": "Luxury Timepieces",
                "claimed_brand": "Apex Brands",
                "img1": ImageEnhance.Contrast(ref_watch.copy()).enhance(1.05),
                "img2": ImageEnhance.Brightness(ref_watch.copy()).enhance(0.96),
                "logo": draw_official_logo("Apex Brands", "distorted", bg=(255, 255, 255), fg=(220, 45, 45)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="APEX CHRONO FLAGSHIP CORP"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": ["https://apex-fake.com"]},
            },
            {
                "case_id": "susp_02_cloned_designer_leather",
                "name": "Luxe Atelier Outlet",
                "category": "Designer Handbags",
                "claimed_brand": "Luxe Atelier",
                "img1": ImageEnhance.Color(ref_bag.copy()).enhance(1.08),
                "img2": ImageEnhance.Contrast(ref_bag.copy()).enhance(1.04),
                "logo": draw_official_logo("Luxe Atelier", "distorted", bg=(20, 20, 20), fg=(255, 60, 60)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="LUXE ATELIER OUTLET TRADING"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": []},
            },
            {
                "case_id": "susp_03_reused_airmax_store",
                "name": "Apex Velocity Sneaker Store",
                "category": "Athletic Footwear",
                "claimed_brand": "Apex Brands",
                "img1": ImageEnhance.Brightness(ref_shoe.copy()).enhance(1.02),
                "img2": ImageEnhance.Contrast(ref_shoe.copy()).enhance(1.06),
                "logo": draw_official_logo("Apex Brands", "distorted", bg=(255, 240, 240), fg=(200, 30, 30)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="APEX VELOCITY SNEAKERS LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": []},
            },
            {
                "case_id": "susp_04_pro_audio_clones",
                "name": "Apex Studio Sound Hub",
                "category": "Wireless Electronics",
                "claimed_brand": "Apex Brands",
                "img1": ImageEnhance.Color(ref_audio.copy()).enhance(1.10),
                "img2": ImageEnhance.Brightness(ref_audio.copy()).enhance(0.95),
                "logo": draw_official_logo("Apex Brands", "distorted", bg=(245, 245, 255), fg=(230, 20, 20)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="APEX STUDIO SOUND HUB INC"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": []},
            },
            {
                "case_id": "susp_05_luxury_gold_horology",
                "name": "Crown & Dial Horology",
                "category": "Luxury Watches",
                "claimed_brand": "Apex Brands",
                "img1": ImageEnhance.Sharpness(ref_watch.copy()).enhance(1.2),
                "img2": ImageEnhance.Color(ref_watch.copy()).enhance(1.05),
                "logo": draw_official_logo("Apex Brands", "distorted", bg=(255, 255, 255), fg=(240, 30, 30)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="CROWN & DIAL HOROLOGY LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": []},
            },
            {
                "case_id": "susp_06_counterfeit_tote_bazaar",
                "name": "Milano Luxury Handbags",
                "category": "Designer Accessories",
                "claimed_brand": "Luxe Atelier",
                "img1": ImageEnhance.Brightness(ref_bag.copy()).enhance(0.98),
                "img2": ImageEnhance.Color(ref_bag.copy()).enhance(1.07),
                "logo": draw_official_logo("Luxe Atelier", "distorted", bg=(255, 245, 245), fg=(220, 40, 40)),
                "doc": draw_official_certificate(is_tampered=True, entity_name="MILANO LUXURY IMPORTS LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": True, "social_links": []},
            },
        ]

        for c in susp_cases:
            sdir = susp_base / c["case_id"]
            sdir.mkdir(parents=True, exist_ok=True)
            c["img1"].save(sdir / "product_1.jpg", quality=90)
            c["img2"].save(sdir / "product_2.jpg", quality=90)
            c["logo"].save(sdir / "logo.png")
            c["doc"].save(sdir / "document.jpg", quality=88)
            meta = {
                "name": c["name"],
                "category": c["category"],
                "claimed_brand": c["claimed_brand"],
                "ground_truth": "HIGH",
                "claims": {
                    "inventory_claim": f"Exclusive authorized inventory and direct stock of {c['category']}.",
                    "brand_claim": f"Official authorized global flagship store for {c['claimed_brand']}.",
                    "compliance_claim": "Statutory Ministry Incorporation Certificate.",
                },
                "crawler_data": c["crawler"],
            }
            with open(sdir / "meta.json", "w") as f:
                json.dump(meta, f, indent=2)

        # ──────────────────────────────────────────────────────────
        # 3. BORDERLINE HELD-OUT TEST CASES (Ground Truth: MEDIUM Risk)
        # ──────────────────────────────────────────────────────────
        bord_base = eval_dir / "borderline"
        bord_base.mkdir(parents=True, exist_ok=True)

        bord_cases = [
            {
                "case_id": "bord_01_urban_distributor",
                "name": "Urban Velocity Footwear",
                "category": "Footwear Reseller",
                "claimed_brand": "Urban Velocity Footwear",
                "img1": draw_realistic_sneaker(primary_color=(105, 120, 145)),
                "logo": draw_official_logo("Urban Velocity", "crest", bg=(32, 35, 45), fg=(175, 180, 195)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="URBAN VELOCITY DISTRIBUTORS"),
                "crawler": {"has_contact": True, "has_policy": False, "has_pricing": True, "has_about": False, "social_links": []},
            },
            {
                "case_id": "bord_02_audio_direct_outlet",
                "name": "Sonic Direct Hub",
                "category": "Consumer Audio",
                "claimed_brand": "Sonic Direct",
                "img1": draw_realistic_headphones(accent_color=(160, 170, 185)),
                "logo": draw_official_logo("Sonic Direct", "crest", bg=(25, 30, 40), fg=(190, 195, 205)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="SONIC DIRECT HUB LLP"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": False, "has_about": False, "social_links": []},
            },
            {
                "case_id": "bord_03_metro_streetwear",
                "name": "Metro Trend Apparel",
                "category": "Urban Streetwear",
                "claimed_brand": "Metro Trend",
                "img1": draw_realistic_sneaker(primary_color=(180, 90, 50)),
                "logo": draw_official_logo("Metro Trend", "crest", bg=(40, 30, 35), fg=(200, 160, 140)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="METRO TREND APPAREL LTD"),
                "crawler": {"has_contact": False, "has_policy": True, "has_pricing": True, "has_about": False, "social_links": []},
            },
            {
                "case_id": "bord_04_commuter_utility_bags",
                "name": "Nomad Utility Gear",
                "category": "Utility Backpacks",
                "claimed_brand": "Nomad Gear",
                "img1": draw_realistic_handbag(leather_color=(60, 70, 80)),
                "logo": draw_official_logo("Nomad Gear", "crest", bg=(30, 35, 45), fg=(160, 175, 190)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="NOMAD UTILITY GEAR INC"),
                "crawler": {"has_contact": True, "has_policy": False, "has_pricing": True, "has_about": False, "social_links": []},
            },
            {
                "case_id": "bord_05_sports_audio_lab",
                "name": "Aero Sound Gear",
                "category": "Athletic Audio",
                "claimed_brand": "Aero Sound",
                "img1": draw_realistic_headphones(accent_color=(200, 120, 40)),
                "logo": draw_official_logo("Aero Sound", "crest", bg=(35, 30, 25), fg=(210, 150, 90)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="AERO SOUND GEAR LTD"),
                "crawler": {"has_contact": True, "has_policy": True, "has_pricing": True, "has_about": False, "social_links": []},
            },
            {
                "case_id": "bord_06_lifestyle_collective",
                "name": "Moda Lifestyle Trading",
                "category": "Lifestyle Accessories",
                "claimed_brand": "Moda Direct",
                "img1": draw_realistic_sneaker(primary_color=(70, 130, 120)),
                "logo": draw_official_logo("Moda Direct", "crest", bg=(20, 35, 35), fg=(140, 190, 180)),
                "doc": draw_official_certificate(is_tampered=False, entity_name="MODA LIFESTYLE TRADING CO"),
                "crawler": {"has_contact": True, "has_policy": False, "has_pricing": False, "has_about": True, "social_links": []},
            },
        ]

        for c in bord_cases:
            bdir = bord_base / c["case_id"]
            bdir.mkdir(parents=True, exist_ok=True)
            c["img1"].save(bdir / "product_1.jpg", quality=90)
            c["logo"].save(bdir / "logo.png")
            c["doc"].save(bdir / "document.jpg", quality=90)
            meta = {
                "name": c["name"],
                "category": c["category"],
                "claimed_brand": c["claimed_brand"],
                "ground_truth": "MEDIUM",
                "claims": {
                    "inventory_claim": f"Regional multi-brand catalog for {c['category']}.",
                    "brand_claim": f"Sub-licensed distribution partner under {c['claimed_brand']}.",
                    "compliance_claim": "Standard digital registration copy.",
                },
                "crawler_data": c["crawler"],
            }
            with open(bdir / "meta.json", "w") as f:
                json.dump(meta, f, indent=2)

    print(f" [✓] Held-out evaluation dataset (18 merchant cases across Clean, Suspicious, Borderline) generated.")


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="🛡️ Visual Consistency & Evidence Engine — Synthetic Dataset Generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Generate both interactive demo cases and held-out evaluation suite (default)",
    )
    group.add_argument(
        "--demo-only",
        action="store_true",
        help="Generate only the 3 interactive demo merchant cases and catalog reference assets",
    )
    group.add_argument(
        "--eval-only",
        action="store_true",
        help="Generate only the 18 held-out evaluation benchmark cases",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential progress output",
    )

    args = parser.parse_args()

    start_time = time.time()

    if not args.quiet:
        print("=" * 75)
        print(" 🛡️  Visual Consistency & Evidence Engine — Dataset Builder")
        print("=" * 75)

    if args.demo_only:
        if not args.quiet:
            print("\n[1/1] Building Reference Catalogs, Brand Marks & Demo Cases...")
        build_all_demo_datasets()
    elif args.eval_only:
        if not args.quiet:
            print("\n[1/1] Building 18 Held-Out Evaluation Cases...")
        build_held_out_evaluation_dataset()
    else:
        if not args.quiet:
            print("\n[1/2] Generating Reference Catalogs, Verified Brands & 3 Demo Cases...")
        build_all_demo_datasets()
        if not args.quiet:
            print("\n[2/2] Generating 18 Held-Out Evaluation Cases (Clean / Borderline / Suspicious)...")
        build_held_out_evaluation_dataset()

    elapsed = time.time() - start_time
    if not args.quiet:
        print("\n" + "=" * 75)
        print(f" [✓] Dataset Generation Complete in {elapsed:.2f}s")
        print(" • Demo Assets Directory:       dataset/merchants/ and backend/dataset/merchants/")
        print(" • Reference Catalogs:          dataset/reference/ and backend/dataset/reference/")
        print(" • Brand Marks:                 dataset/logos/ and backend/dataset/logos/")
        print(" • Held-Out Evaluation Suite:   backend/dataset/eval_set/ (18 test cases)")
        print("=" * 75)


if __name__ == "__main__":
    main()

