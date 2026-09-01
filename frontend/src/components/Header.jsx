import React from 'react';
import { Shield, ShieldCheck, Globe, Cpu, Layers } from 'lucide-react';

export default function Header() {
  return (
    <>
      <div className="prototype-banner">
        <ShieldCheck size={18} color="#38bdf8" style={{ flexShrink: 0 }} />
        <div>
          <strong style={{ color: '#ffffff' }}>DECISION-SUPPORT SYSTEM FOR HUMAN RISK ANALYSTS:</strong> This engine produces explainable empirical visual signals to assist risk reviewers. It <span style={{ textDecoration: 'underline' }}>never</span> automatically rejects merchants or declares fraud verdicts.
        </div>
      </div>

      <header className="main-header">
        <div>
          <div className="header-brand">
            <Shield size={32} color="#3b82f6" />
            <span>Visual Consistency & Evidence Engine</span>
          </div>
          <p>
            Multimodal visual intelligence, online candidate discovery (Serper.dev) & ViT verification for merchant underwriting
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
          <div className="status-pill emerald" title="Online Evidence Discovery via Serper.dev / Web Search">
            <span className="pulse-dot emerald"></span>
            <Globe size={14} />
            <span>Serper.dev Web Search</span>
          </div>

          <div className="status-pill blue" title="Vision Transformer ViT-B/16 Pre-Warmed">
            <Cpu size={14} />
            <span>ViT-B/16 Backbone</span>
          </div>

          <div className="status-pill purple" title="Dual-Layer Evidence Corroboration">
            <Layers size={14} />
            <span>Multimodal Fusion</span>
          </div>
        </div>
      </header>
    </>
  );
}
