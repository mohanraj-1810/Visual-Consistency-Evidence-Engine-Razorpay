import React from 'react';
import { Shield, ShieldAlert, Sparkles } from 'lucide-react';

export default function Header() {
  return (
    <>
      <div className="prototype-banner">
        <ShieldAlert size={18} color="#60a5fa" style={{ flexShrink: 0 }} />
        <div>
          <strong>DECISION-SUPPORT PROTOTYPE FOR HUMAN RISK ANALYSTS:</strong> This engine produces explainable empirical visual signals to assist risk reviewers. It <strong>never</strong> automatically rejects merchants or declares fraud verdicts.
        </div>
      </div>

      <header className="main-header">
        <div>
          <h1>
            <Shield size={32} color="#6366f1" />
            Visual Consistency & Evidence Engine
          </h1>
          <p>Explainable visual evidence and multimodal risk fusion for merchant onboarding & risk operations</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="header-badge">
            <Sparkles size={13} style={{ display: 'inline', marginRight: '4px', verticalAlign: '-1px' }} />
            Razorpay Track 02: AI Risk Manager
          </span>
        </div>
      </header>
    </>
  );
}
