import React from 'react';
import { Scale, ShoppingBag, Award, FileCheck2, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function ClaimVsEvidence({ claims, reuse, logo, manipulation }) {
  if (!claims) return null;

  const topItem = reuse?.top_flagged_item;
  const topSim = topItem?.similarity ?? 0.0;
  const refName = topItem?.reference_filename ?? 'None';
  const logoSim = logo?.similarity ?? 1.0;
  const logoConsistency = logo?.consistency_score ?? 100;
  const manipScore = manipulation?.manipulation_score ?? 0.0;

  const isReuseHigh = topSim >= 0.80;
  const isLogoDivergent = logoSim < 0.65;
  const isManipHigh = manipScore >= 40.0;

  return (
    <div style={{ marginBottom: '2rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Scale size={20} color="#6366f1" />
          Claim vs. Visual Evidence Matrix
        </h3>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
          Direct side-by-side comparison answering: <em>«Does the visual evidence on this merchant support or contradict what the merchant claims?»</em>
        </p>
      </div>

      <div className="matrix-grid">
        {/* Dimension 1: Inventory */}
        <div className="matrix-col">
          <h4>
            <ShoppingBag size={18} color="#60a5fa" />
            1. Inventory & Products
          </h4>
          <div className="claim-box">
            <div className="claim-box-title">Merchant Claim</div>
            <div className="claim-box-content">{claims.inventory_claim || 'Authentic proprietary inventory'}</div>
          </div>
          <div className={`reality-box ${isReuseHigh ? 'red' : 'green'}`}>
            <div className={`reality-box-title ${isReuseHigh ? 'red' : 'green'}`}>
              {isReuseHigh ? '⚠️ CONTRADICTS (High Catalog Reuse)' : '✅ SUPPORTS (Original Photography)'}
            </div>
            <div className="claim-box-content">
              <strong>ViT Similarity:</strong> {Math.round(topSim * 100)}% match with reference catalog <code>{refName}</code>.
            </div>
          </div>
        </div>

        {/* Dimension 2: Brand Logo */}
        <div className="matrix-col">
          <h4>
            <Award size={18} color="#a855f7" />
            2. Brand Identity & Logo
          </h4>
          <div className="claim-box">
            <div className="claim-box-title">Merchant Claim</div>
            <div className="claim-box-content">{claims.brand_claim || 'Verified brand trademark'}</div>
          </div>
          <div className={`reality-box ${isLogoDivergent ? 'red' : 'green'}`}>
            <div className={`reality-box-title ${isLogoDivergent ? 'red' : 'green'}`}>
              {isLogoDivergent ? '⚠️ CONTRADICTS (Stylistic Divergence)' : '✅ SUPPORTS (Consistent Identity)'}
            </div>
            <div className="claim-box-content">
              <strong>Logo Consistency:</strong> {logoConsistency}% match vs official brand mark reference asset.
            </div>
          </div>
        </div>

        {/* Dimension 3: Document Integrity */}
        <div className="matrix-col">
          <h4>
            <FileCheck2 size={18} color="#10b981" />
            3. Document Integrity
          </h4>
          <div className="claim-box">
            <div className="claim-box-title">Merchant Claim</div>
            <div className="claim-box-content">{claims.compliance_claim || 'Statutory incorporation certificate'}</div>
          </div>
          <div className={`reality-box ${isManipHigh ? 'red' : 'green'}`}>
            <div className={`reality-box-title ${isManipHigh ? 'red' : 'green'}`}>
              {isManipHigh ? '⚠️ CONTRADICTS (Splicing Anomaly)' : '✅ SUPPORTS (Uniform Compression)'}
            </div>
            <div className="claim-box-content">
              <strong>Forensic Anomaly Score:</strong> {manipScore}% localized compression variance & edge tampering.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
