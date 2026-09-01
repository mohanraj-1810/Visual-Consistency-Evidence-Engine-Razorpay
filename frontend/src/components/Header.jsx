import React from 'react';
import { ShieldCheck, Globe, Cpu, Layers, Shield } from 'lucide-react';

export default function Header() {
  return (
    <>
      {/* ── Top compliance banner ── */}
      <div className="compliance-banner">
        <ShieldCheck size={15} className="compliance-banner__icon" />
        <span>
          <strong>DECISION-SUPPORT SYSTEM FOR HUMAN RISK ANALYSTS:</strong>{' '}
          This engine produces explainable empirical visual signals to assist risk reviewers.
          It <u>never</u> automatically rejects merchants or declares fraud verdicts.
        </span>
      </div>

      {/* ── Main sticky nav header ── */}
      <header className="site-header">
        <div className="site-header__inner">

          {/* Brand lockup */}
          <div className="site-header__brand">
            <div className="site-header__logo">
              <Shield size={22} color="#3b82f6" />
            </div>
            <div>
              <div className="site-header__name">Visual Consistency &amp; Evidence Engine</div>
              <div className="site-header__sub">Merchant Visual Risk Intelligence · Razorpay</div>
            </div>
          </div>

          {/* Status pills */}
          <div className="site-header__pills">
            <div className="status-pill status-pill--green" title="Online Evidence Discovery via Serper.dev">
              <span className="status-pill__dot status-pill__dot--pulse" />
              <Globe size={12} />
              <span>Serper.dev</span>
            </div>

            <div className="status-pill status-pill--blue" title="Vision Transformer ViT-B/16 Pre-Warmed">
              <Cpu size={12} />
              <span>ViT-B/16</span>
            </div>

            <div className="status-pill status-pill--purple" title="Dual-Layer Multimodal Evidence Fusion">
              <Layers size={12} />
              <span>Fusion</span>
            </div>
          </div>

        </div>
      </header>
    </>
  );
}
