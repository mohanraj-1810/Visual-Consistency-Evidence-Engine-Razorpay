import React, { useState, useEffect } from 'react';
import { Database, Globe, Upload, Play, CheckCircle2, AlertCircle } from 'lucide-react';
import { fetchDemoCases } from '../api/client';

export default function MerchantForm({ onAnalyze, loading }) {
  const [mode, setMode] = useState('demo'); // 'demo' | 'url' | 'upload'
  const [demoCases, setDemoCases] = useState([]);
  const [selectedDemo, setSelectedDemo] = useState('Suspicious Merchant');
  
  // URL mode state
  const [targetUrl, setTargetUrl] = useState('https://example.com');
  const [claimedBrandUrl, setClaimedBrandUrl] = useState('Apex Brands');
  const [merchantNameUrl, setMerchantNameUrl] = useState('');

  // Upload mode state
  const [productFiles, setProductFiles] = useState([]);
  const [logoFile, setLogoFile] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [merchantNameUpload, setMerchantNameUpload] = useState('Custom Merchant');
  const [claimedBrandUpload, setClaimedBrandUpload] = useState('Apex Brands');
  const [claimInventory, setClaimInventory] = useState('Exclusive authorized dealer with proprietary inventory.');
  const [claimBrand, setClaimBrand] = useState('Official flagship partner store.');
  const [claimCompliance, setClaimCompliance] = useState('Statutory ministry incorporation certificate.');

  useEffect(() => {
    fetchDemoCases()
      .then((data) => {
        setDemoCases(data);
        if (data.length > 0) {
          setSelectedDemo(data[0].id);
        }
      })
      .catch((err) => {
        console.warn('Could not fetch demo cases from backend, using fallback list', err);
        setDemoCases([
          { id: 'Suspicious Merchant', name: 'Apex Global Luxury Store', category: 'Luxury Watches & Handbags' },
          { id: 'Clean Merchant', name: 'Earth & Clay Studio', category: 'Handcrafted Goods' },
          { id: 'Borderline Merchant', name: 'Urban Velocity Store', category: 'Footwear & Apparel' },
        ]);
      });
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('mode', mode);

    if (mode === 'demo') {
      formData.append('demo_case', selectedDemo);
    } else if (mode === 'url') {
      formData.append('target_url', targetUrl);
      formData.append('claimed_brand', claimedBrandUrl);
      if (merchantNameUrl) formData.append('merchant_name', merchantNameUrl);
    } else if (mode === 'upload') {
      formData.append('merchant_name', merchantNameUpload);
      formData.append('claimed_brand', claimedBrandUpload);
      formData.append('claim_inventory', claimInventory);
      formData.append('claim_brand', claimBrand);
      formData.append('claim_compliance', claimCompliance);

      for (let i = 0; i < productFiles.length; i++) {
        formData.append('product_images', productFiles[i]);
      }
      if (logoFile) formData.append('logo_image', logoFile);
      if (docFile) formData.append('document_image', docFile);
    }

    onAnalyze(formData);
  };

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="card-title">
        <Database size={18} color="#6366f1" />
        Merchant Risk Ingestion & Ingestion Controller
      </div>
      <div className="card-subtitle">
        Select ingestion stream: Controlled empirical benchmark, live merchant URL crawler, or manual forensic dossier upload.
      </div>

      <div className="mode-tabs">
        <button
          type="button"
          className={`mode-tab-btn ${mode === 'demo' ? 'active' : ''}`}
          onClick={() => setMode('demo')}
        >
          <Database size={15} />
          Mode A — Demo Case (Offline Benchmark)
        </button>
        <button
          type="button"
          className={`mode-tab-btn ${mode === 'url' ? 'active' : ''}`}
          onClick={() => setMode('url')}
        >
          <Globe size={15} />
          Mode B — Live Merchant URL
        </button>
        <button
          type="button"
          className={`mode-tab-btn ${mode === 'upload' ? 'active' : ''}`}
          onClick={() => setMode('upload')}
        >
          <Upload size={15} />
          Mode C — Manual File Upload
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {mode === 'demo' && (
          <div>
            <div className="form-group">
              <label className="form-label">Select Merchant Benchmark Case</label>
              <select
                className="form-select"
                value={selectedDemo}
                onChange={(e) => setSelectedDemo(e.target.value)}
              >
                {demoCases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name ? `${c.id} — ${c.name} (${c.category || ''})` : c.id}
                  </option>
                ))}
              </select>
            </div>

            {demoCases.find((c) => c.id === selectedDemo) && (
              <div
                style={{
                  background: '#0f172a',
                  padding: '0.85rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid #334155',
                  marginBottom: '1rem',
                  fontSize: '0.85rem',
                  color: '#cbd5e1',
                }}
              >
                <strong>Case Description:</strong>{' '}
                {demoCases.find((c) => c.id === selectedDemo)?.description}
              </div>
            )}
          </div>
        )}

        {mode === 'url' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Merchant Website URL</label>
              <input
                type="url"
                className="form-input"
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                placeholder="https://merchant-store.com"
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Claimed Brand</label>
              <input
                type="text"
                className="form-input"
                value={claimedBrandUrl}
                onChange={(e) => setClaimedBrandUrl(e.target.value)}
                placeholder="e.g. Apex Brands"
              />
            </div>
            <div className="form-group">
              <label className="form-label">Merchant Name (Optional)</label>
              <input
                type="text"
                className="form-input"
                value={merchantNameUrl}
                onChange={(e) => setMerchantNameUrl(e.target.value)}
                placeholder="Auto-detected from domain"
              />
            </div>
          </div>
        )}

        {mode === 'upload' && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Merchant / Business Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={merchantNameUpload}
                  onChange={(e) => setMerchantNameUpload(e.target.value)}
                  placeholder="e.g. Nova Retail Ltd"
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Claimed Brand / Trademark</label>
                <input
                  type="text"
                  className="form-input"
                  value={claimedBrandUpload}
                  onChange={(e) => setClaimedBrandUpload(e.target.value)}
                  placeholder="e.g. Apex Brands"
                  required
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group">
                <label className="form-label">1. Product Images</label>
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  className="form-input"
                  onChange={(e) => setProductFiles(Array.from(e.target.files || []))}
                />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  {productFiles.length > 0 ? `${productFiles.length} file(s) selected` : 'Select catalog photos'}
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">2. Merchant Logo</label>
                <input
                  type="file"
                  accept="image/*"
                  className="form-input"
                  onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  {logoFile ? logoFile.name : 'Select official brand mark'}
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">3. Certificate / Invoice</label>
                <input
                  type="file"
                  accept="image/*"
                  className="form-input"
                  onChange={(e) => setDocFile(e.target.files?.[0] || null)}
                />
                <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                  {docFile ? docFile.name : 'Select statutory certificate'}
                </span>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Inventory Self-Claim</label>
                <textarea
                  rows={2}
                  className="form-textarea"
                  value={claimInventory}
                  onChange={(e) => setClaimInventory(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Brand Authorization Claim</label>
                <textarea
                  rows={2}
                  className="form-textarea"
                  value={claimBrand}
                  onChange={(e) => setClaimBrand(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Compliance Disclosure Claim</label>
                <textarea
                  rows={2}
                  className="form-textarea"
                  value={claimCompliance}
                  onChange={(e) => setClaimCompliance(e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '0.75rem' }}>
          {loading ? (
            <>
              <div className="spinner" />
              Running Multimodal ViT & Forensic Pipeline...
            </>
          ) : (
            <>
              <Play size={16} fill="currentColor" />
              Execute Multimodal Risk Analysis
            </>
          )}
        </button>
      </form>
    </div>
  );
}
