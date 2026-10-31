import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  FileText,
  UploadCloud,
  Layers,
  Activity,
  Search,
  Filter,
  RefreshCw,
  Building,
  Zap,
  Eye,
  PlusCircle,
  ExternalLink,
  ChevronRight,
  Database,
  ArrowRight,
  BookOpen,
  Gauge
} from 'lucide-react';
import './App.css';
import logo from './assets/logo.png';

const API_BASE = 'http://localhost:8000/api/v1';

function PrecursorConfidenceIndicator({ report, compact = false }) {
  if (!report) return null;

  const rawScore = report.confidence_score;
  const isUnavailable = rawScore === null || rawScore === undefined || report.confidence_band === 'Unavailable';

  let percentage = null;
  if (!isUnavailable) {
    if (rawScore > 1.0) {
      percentage = Math.round(rawScore);
    } else if (rawScore > 0.0) {
      percentage = Math.round(rawScore * 100);
    } else {
      percentage = 0;
    }
  }

  let band = report.confidence_band;
  if (!band || band === 'Unavailable') {
    if (isUnavailable) {
      band = 'Confidence unavailable — insufficient evidence';
    } else if (percentage >= 80) {
      band = 'High Confidence';
    } else if (percentage >= 60) {
      band = 'Moderate Confidence';
    } else {
      band = 'Low Confidence';
    }
  }

  // Visual Palette
  let color = 'var(--text-secondary)';
  let bgBadge = 'rgba(162, 168, 168, 0.12)';
  if (!isUnavailable) {
    if (percentage >= 80) {
      color = 'var(--verified-green)';
      bgBadge = 'rgba(53, 168, 121, 0.15)';
    } else if (percentage >= 60) {
      color = 'var(--safety-amber)';
      bgBadge = 'rgba(242, 169, 0, 0.15)';
    } else {
      color = 'var(--critical-red)';
      bgBadge = 'rgba(224, 82, 82, 0.15)';
    }
  }

  const explanationText = report.confidence_explanation || (
    isUnavailable
      ? 'Confidence unavailable — insufficient evidence. The report narrative contains insufficient factual detail to evaluate hazard presence or safety barrier integrity.'
      : report.sif_precursor_flag
      ? `SAJAG identified a potential SIF precursor based on available physical evidence and safeguard telemetry.`
      : `Evaluated as ${report.risk_priority?.replace('_', ' ') || 'routine observation'} with intact baseline safeguards.`
  );

  const supportingEvidence = report.confidence_supporting_evidence || [];
  const missingInfo = report.confidence_missing_information || [];

  return (
    <div
      className="precursor-confidence-indicator"
      style={{
        background: 'var(--bg-panel-secondary)',
        border: '1px solid var(--border-divider)',
        borderRadius: 'var(--radius-sm)',
        padding: compact ? '10px 12px' : '14px 16px',
        marginTop: compact ? 8 : 12,
        marginBottom: compact ? 10 : 20
      }}
    >
      {/* Title Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Gauge size={14} style={{ color }} />
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              color: 'var(--text-muted)'
            }}
          >
            Precursor Detection Confidence
          </span>
        </div>
        <span
          style={{
            fontSize: '0.675rem',
            padding: '2px 6px',
            borderRadius: 2,
            background: bgBadge,
            color,
            fontWeight: 700
          }}
        >
          {isUnavailable ? 'Insufficient Evidence' : `${band.replace(' Confidence', '')} Band`}
        </span>
      </div>

      {/* Main Score & Band Display */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 8 }}>
        {!isUnavailable ? (
          <>
            <span
              style={{
                fontSize: compact ? '1.15rem' : '1.35rem',
                fontWeight: 800,
                fontFamily: 'monospace',
                color
              }}
            >
              {percentage}%
            </span>
            <span style={{ fontSize: compact ? '0.85rem' : '0.95rem', fontWeight: 700, color }}>
              — {band}
            </span>
          </>
        ) : (
          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
            Confidence unavailable — insufficient evidence
          </span>
        )}
      </div>

      {/* Horizontal Progress Bar */}
      {!isUnavailable && (
        <div
          style={{
            width: '100%',
            height: compact ? 6 : 8,
            background: 'var(--bg-main)',
            borderRadius: 2,
            overflow: 'hidden',
            border: '1px solid var(--border-divider)',
            marginBottom: 10
          }}
        >
          <div
            style={{
              width: `${Math.max(0, Math.min(100, percentage))}%`,
              height: '100%',
              backgroundColor: color,
              borderRadius: 2,
              transition: 'width 0.25s ease'
            }}
          />
        </div>
      )}

      {/* Explanation Text */}
      <p style={{ fontSize: '0.785rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: (supportingEvidence.length > 0 || missingInfo.length > 0) ? 8 : 4 }}>
        "{explanationText}"
      </p>

      {/* Main Evidence Supporting & Missing Information (if not compact) */}
      {!compact && (supportingEvidence.length > 0 || missingInfo.length > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: supportingEvidence.length > 0 && missingInfo.length > 0 ? '1fr 1fr' : '1fr', gap: 8, marginTop: 8, marginBottom: 8, fontSize: '0.725rem' }}>
          {supportingEvidence.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '6px 8px', borderRadius: 2, border: '1px solid var(--border-divider)' }}>
              <div style={{ color: 'var(--verified-green)', fontWeight: 700, marginBottom: 4 }}>
                ✔ Supporting Evidence
              </div>
              <ul style={{ listStyle: 'none', paddingLeft: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 3, color: 'var(--text-secondary)' }}>
                {supportingEvidence.slice(0, 3).map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
                    <span style={{ color: 'var(--verified-green)' }}>•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {missingInfo.length > 0 && (
            <div style={{ background: 'var(--bg-input)', padding: '6px 8px', borderRadius: 2, border: '1px solid var(--border-divider)' }}>
              <div style={{ color: 'var(--safety-amber)', fontWeight: 700, marginBottom: 4 }}>
                ⚠️ Missing / Ambiguous Information
              </div>
              <ul style={{ listStyle: 'none', paddingLeft: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 3, color: 'var(--text-secondary)' }}>
                {missingInfo.slice(0, 2).map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 4 }}>
                    <span style={{ color: 'var(--safety-amber)' }}>•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Separate Concepts Notice */}
      <div
        style={{
          borderTop: '1px solid var(--border-divider)',
          paddingTop: 6,
          marginTop: 6,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.675rem',
          color: 'var(--text-dim)',
          gap: 4
        }}
      >
        <span>
          <strong>Rule-based confidence estimate</strong> • Bands: 80–100% High, 60–79% Moderate, &lt;60% Low (provisional non-statistical thresholds)
        </span>
        <span style={{ color: 'var(--text-muted)' }}>
          Independent of Risk Severity &amp; Actual Outcome
        </span>
      </div>
    </div>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('queue');
  const [reports, setReports] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [similarIncidents, setSimilarIncidents] = useState([]);
  const [actions, setActions] = useState([]);
  const [crossSiteData, setCrossSiteData] = useState(null);
  const [benchmarkEvaluation, setBenchmarkEvaluation] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // AI Safety Document Intelligence & Q&A State
  const [kbSubTab, setKbSubTab] = useState('qa'); // 'qa', 'search', 'upload'
  const [qaQuery, setQaQuery] = useState('');
  const [qaResult, setQaResult] = useState(null);
  const [qaLoading, setQaLoading] = useState(false);
  const [kbQuery, setKbQuery] = useState('');
  const [kbResults, setKbResults] = useState([]);
  const [kbFilterReport, setKbFilterReport] = useState('');
  const [kbFilterFactType, setKbFilterFactType] = useState('');
  const [kbFilterIogp, setKbFilterIogp] = useState('');
  const [kbLoading, setKbLoading] = useState(false);
  const [kbSummary, setKbSummary] = useState(null);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [pdfFile, setPdfFile] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterFacility, setFilterFacility] = useState('');
  const [sifOnly, setSifOnly] = useState(false);

  // Manual Ingestion Form State
  const [newReport, setNewReport] = useState({
    facility: 'Gulf Coast Refinery',
    unit_or_area: 'Crude Distillation Unit (CDU-1)',
    report_date: new Date().toISOString().split('T')[0],
    incident_type: 'near_miss',
    activity: 'Maintenance',
    reporter_role: 'Operations Lead',
    actual_outcome: 'Near Miss (No Physical Harm)',
    description: ''
  });
  const [livePreview, setLivePreview] = useState(null);

  // Action Creation Modal
  const [actionModalOpen, setActionModalOpen] = useState(false);
  const [actionReport, setActionReport] = useState(null);
  const [recommendedControls, setRecommendedControls] = useState([]);
  const [actionForm, setActionForm] = useState({
    title: '',
    description: '',
    hierarchy_level: 'Engineering Controls',
    owner_name: '',
    owner_department: 'Operations & Maintenance',
    target_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
  });

  // Verification Gate Modal
  const [verifyModalOpen, setVerifyModalOpen] = useState(false);
  const [verifyingAction, setVerifyingAction] = useState(null);
  const [verificationForm, setVerificationForm] = useState({
    verified_by: '',
    verification_notes: '',
    verification_attachment: ''
  });

  // Toast Notification
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Fetch Core Data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [reportsRes, kpisRes, actionsRes] = await Promise.all([
        fetch(`${API_BASE}/reports?limit=150`),
        fetch(`${API_BASE}/analytics/kpis`),
        fetch(`${API_BASE}/actions`)
      ]);

      if (reportsRes.ok) {
        const data = await reportsRes.json();
        setReports(data);
        if (data.length > 0 && !selectedReport) {
          setSelectedReport(data[0]);
        }
      }
      if (kpisRes.ok) {
        setKpis(await kpisRes.json());
      }
      if (actionsRes.ok) {
        setActions(await actionsRes.json());
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Fetch Similar Incidents when selectedReport changes
  useEffect(() => {
    if (selectedReport) {
      fetch(`${API_BASE}/recurrence/similar/${selectedReport.id}`)
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) setSimilarIncidents(data.similar_incidents || []);
        })
        .catch(console.error);
    }
  }, [selectedReport]);

  // Live AI Preview Debounce for Manual Entry
  useEffect(() => {
    if (newReport.description.trim().length > 15) {
      const timer = setTimeout(() => {
        fetch(`${API_BASE}/reports/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            description: newReport.description,
            reported_outcome: newReport.actual_outcome
          })
        })
          .then((r) => (r.ok ? r.json() : null))
          .then((data) => {
            if (data) setLivePreview(data);
          })
          .catch(console.error);
      }, 350);
      return () => clearTimeout(timer);
    } else {
      setLivePreview(null);
    }
  }, [newReport.description, newReport.actual_outcome]);

  // Fetch Cross-Site Summary
  const fetchCrossSiteData = async () => {
    try {
      const res = await fetch(`${API_BASE}/recurrence/cross-site-summary`);
      if (res.ok) setCrossSiteData(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  // Fetch Benchmark Evaluation
  const fetchBenchmarkEvaluation = async () => {
    try {
      const res = await fetch(`${API_BASE}/benchmark/evaluate`);
      if (res.ok) setBenchmarkEvaluation(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const fetchKbSummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/knowledge/summary`);
      if (res.ok) setKbSummary(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleQaAsk = async (overrideQuery = null) => {
    const q = overrideQuery !== null ? overrideQuery : qaQuery;
    if (!q || !q.trim()) return;
    setQaLoading(true);
    try {
      const res = await fetch(`${API_BASE}/knowledge/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          filter_report: kbFilterReport || null,
          top_k: 6
        })
      });
      if (res.ok) {
        const data = await res.json();
        setQaResult(data);
      } else {
        showToast('❌ Error executing Document Q&A');
      }
    } catch (err) {
      console.error(err);
      showToast('❌ Network error during Q&A');
    } finally {
      setQaLoading(false);
    }
  };

  const handlePdfUpload = async (e) => {
    e.preventDefault();
    if (!pdfFile) {
      showToast('⚠️ Please select a PDF file first.');
      return;
    }
    setUploadingPdf(true);
    const formData = new FormData();
    formData.append('file', pdfFile);
    try {
      const res = await fetch(`${API_BASE}/knowledge/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`✅ Ingested ${pdfFile.name} (${data.details.chunks_added} chunks)!`);
        setPdfFile(null);
        await fetchKbSummary();
      } else {
        const err = await res.json();
        showToast(`❌ Upload failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (err) {
      showToast('❌ Upload failed due to network error.');
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleKbSearch = async (overrideQuery = null) => {
    const q = overrideQuery !== null ? overrideQuery : kbQuery;
    if (!q || !q.trim()) return;
    setKbLoading(true);
    try {
      let url = `${API_BASE}/knowledge/search?query=${encodeURIComponent(q)}&top_k=8`;
      if (kbFilterReport) url += `&filter_report=${encodeURIComponent(kbFilterReport)}`;
      if (kbFilterFactType) url += `&filter_fact_type=${encodeURIComponent(kbFilterFactType)}`;
      if (kbFilterIogp) url += `&filter_iogp=${encodeURIComponent(kbFilterIogp)}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setKbResults(data.results || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setKbLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'recurrence') fetchCrossSiteData();
    if (activeTab === 'benchmark') fetchBenchmarkEvaluation();
    if (activeTab === 'library') {
      fetchKbSummary();
      if (!qaResult) {
        const initialQ = 'What caused the naphtha fire at IOCL Haldia refinery and which safeguards failed?';
        setQaQuery(initialQ);
        handleQaAsk(initialQ);
      }
      if (!kbQuery) {
        setKbQuery('naphtha fire reboiler drain gas cutting');
        handleKbSearch('naphtha fire reboiler drain gas cutting');
      }
    }
  }, [activeTab]);

  // Seed Benchmark
  const handleSeedBenchmark = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/benchmark/seed`, { method: 'POST' });
      if (res.ok) {
        showToast('✅ Benchmark dataset seeded successfully!');
        await fetchData();
        if (activeTab === 'benchmark') fetchBenchmarkEvaluation();
      }
    } catch (err) {
      showToast('❌ Error seeding benchmark data');
    } finally {
      setLoading(false);
    }
  };

  // Submit Manual Report
  const handleCreateReport = async (e) => {
    e.preventDefault();
    if (!newReport.description.trim()) {
      showToast('⚠️ Please enter an incident description.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newReport)
      });
      if (res.ok) {
        const created = await res.json();
        showToast(`✅ Report ${created.report_uid} triaged as ${created.risk_priority}`);
        setNewReport({
          facility: 'Gulf Coast Refinery',
          unit_or_area: 'Crude Distillation Unit (CDU-1)',
          report_date: new Date().toISOString().split('T')[0],
          incident_type: 'near_miss',
          activity: 'Maintenance',
          reporter_role: 'Operations Lead',
          actual_outcome: 'Near Miss (No Physical Harm)',
          description: ''
        });
        setLivePreview(null);
        await fetchData();
        setSelectedReport(created);
        setActiveTab('inspector');
      }
    } catch (err) {
      showToast('❌ Error creating report');
    }
  };

  // Batch File Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/reports/upload`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        showToast(`✅ ${data.message}`);
        await fetchData();
        setActiveTab('queue');
      } else {
        const err = await res.json();
        showToast(`❌ Upload failed: ${err.detail}`);
      }
    } catch (err) {
      showToast('❌ Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  // Open Action Modal
  const openActionModal = async (report) => {
    setActionReport(report);
    setActionForm({
      title: `Remediate ${report.energy_source} hazard`,
      description: `Implement verified control on barrier: ${report.barrier_name}`,
      hierarchy_level: report.sif_precursor_flag ? 'Engineering Controls' : 'Administrative Controls',
      owner_name: '',
      owner_department: 'Operations',
      target_date: new Date(Date.now() + 7 * 86400000).toISOString().split('T')[0]
    });
    try {
      const res = await fetch(`${API_BASE}/actions/recommendations/${report.id}`);
      if (res.ok) {
        const data = await res.json();
        setRecommendedControls(data.recommendations || []);
      }
    } catch (err) {
      console.error(err);
    }
    setActionModalOpen(true);
  };

  // Create Action
  const handleSaveAction = async (e) => {
    e.preventDefault();
    if (!actionForm.owner_name.trim()) {
      showToast('⚠️ Action assignee owner name is required.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/actions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...actionForm,
          report_id: actionReport.id
        })
      });
      if (res.ok) {
        showToast('✅ Corrective Action created with strict verification gate.');
        setActionModalOpen(false);
        await fetchData();
        setActiveTab('actions');
      }
    } catch (err) {
      showToast('❌ Error creating action');
    }
  };

  // Open Verification Modal
  const openVerifyModal = (action) => {
    setVerifyingAction(action);
    setVerificationForm({
      verified_by: '',
      verification_notes: '',
      verification_attachment: 'physical_inspection_signoff.pdf'
    });
    setVerifyModalOpen(true);
  };

  // Submit Verification Gate
  const handleVerifyAction = async (e) => {
    e.preventDefault();
    if (!verificationForm.verified_by.trim() || verificationForm.verification_notes.length < 10) {
      showToast('⚠️ Strict Gate: Authorized verifier & 10+ char evidence notes required.');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/actions/${verifyingAction.id}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(verificationForm)
      });
      if (res.ok) {
        showToast('🛡️ Action verified and closed with auditable evidence!');
        setVerifyModalOpen(false);
        await fetchData();
      } else {
        const err = await res.json();
        showToast(`❌ Verification rejected: ${err.detail}`);
      }
    } catch (err) {
      showToast('❌ Verification error');
    }
  };

  // Filtered reports
  const filteredReports = reports.filter((r) => {
    if (sifOnly && !r.sif_precursor_flag) return false;
    if (filterPriority && r.risk_priority !== filterPriority) return false;
    if (filterFacility && r.facility !== filterFacility) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        r.description.toLowerCase().includes(q) ||
        r.energy_source.toLowerCase().includes(q) ||
        r.report_uid.toLowerCase().includes(q) ||
        r.facility.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="app-container" id="sajag-root-app">
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          background: 'rgba(15, 23, 42, 0.95)',
          border: '1px solid var(--accent-cyan)',
          color: '#fff',
          padding: '12px 20px',
          borderRadius: 8,
          boxShadow: '0 4px 24px rgba(0,0,0,0.8)',
          zIndex: 999,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          fontSize: '0.9rem'
        }}>
          {toastMessage}
        </div>
      )}

      {/* Workstation Top Navigation & System Status */}
      <header className="app-header">
        <div className="brand-section">
          <img src={logo} alt="SAJAG Logo" className="brand-logo" />
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <h1 className="brand-title">SAJAG</h1>
            <span style={{ color: 'var(--border-divider)', fontSize: '0.8rem' }}>|</span>
            <p className="brand-subtitle">Industrial Safety Surveillance & SIF Workstation</p>
          </div>
        </div>

        <div className="header-status-pills">
          <div className="status-pill">
            <div className="status-dot"></div>
            <span>SYS: ONLINE</span>
          </div>
          <div className="status-pill" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Zap size={11} style={{ color: 'var(--safety-amber)' }} />
            <span>SIF ENGINE: ACTIVE</span>
          </div>
          <div className="status-pill" style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <Database size={11} style={{ color: 'var(--text-secondary)' }} />
            <span>SQLITE AUDITABLE</span>
          </div>
          <button className="btn btn-secondary" style={{ padding: '3px 8px', fontSize: '0.725rem' }} onClick={handleSeedBenchmark} id="seed-benchmark-btn">
            <RefreshCw size={11} />
            <span>Seed Benchmark</span>
          </button>
          <button className="btn btn-primary" style={{ padding: '3px 8px', fontSize: '0.725rem' }} onClick={fetchData} id="refresh-data-btn">
            <RefreshCw size={11} className={loading ? 'pulse-glow' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </header>

      {/* Workstation Layout Shell */}
      <div className="workstation-layout">
        {/* Left Sidebar Navigation */}
        <aside className="workstation-sidebar">
          <div>
            <div className="sidebar-section-title">Navigation Modules</div>
            <nav className="sidebar-nav">
              <button
                className={`sidebar-tab ${activeTab === 'queue' ? 'active' : ''}`}
                onClick={() => setActiveTab('queue')}
                id="tab-queue"
              >
                <AlertTriangle size={15} />
                <span>01. Triage & Incident Queue</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'inspector' ? 'active' : ''}`}
                onClick={() => setActiveTab('inspector')}
                id="tab-inspector"
              >
                <Eye size={15} />
                <span>02. SIF Precursor Inspector</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'ingest' ? 'active' : ''}`}
                onClick={() => setActiveTab('ingest')}
                id="tab-ingest"
              >
                <UploadCloud size={15} />
                <span>03. Report Ingestion Hub</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'actions' ? 'active' : ''}`}
                onClick={() => setActiveTab('actions')}
                id="tab-actions"
              >
                <CheckCircle size={15} />
                <span>04. Controls & Verification</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'recurrence' ? 'active' : ''}`}
                onClick={() => setActiveTab('recurrence')}
                id="tab-recurrence"
              >
                <Layers size={15} />
                <span>05. Recurrence & Cross-Site</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'analytics' ? 'active' : ''}`}
                onClick={() => setActiveTab('analytics')}
                id="tab-analytics"
              >
                <Activity size={15} />
                <span>06. Plant Analytics</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'benchmark' ? 'active' : ''}`}
                onClick={() => setActiveTab('benchmark')}
                id="tab-benchmark"
              >
                <FileText size={15} />
                <span>07. Benchmark Suite</span>
              </button>
              <button
                className={`sidebar-tab ${activeTab === 'library' ? 'active' : ''}`}
                onClick={() => setActiveTab('library')}
                id="tab-library"
              >
                <BookOpen size={15} />
                <span>08. Safety Knowledge Q&A</span>
              </button>
            </nav>
          </div>

          {/* Sidebar Telemetry Summary */}
          {kpis && (
            <div className="sidebar-telemetry">
              <div className="sidebar-section-title" style={{ padding: '0 0 4px 0' }}>Plant Telemetry</div>
              <div className="sidebar-telemetry-row">
                <span className="sidebar-telemetry-label">Ingested:</span>
                <span className="sidebar-telemetry-val">{kpis.summary.total_reports}</span>
              </div>
              <div className="sidebar-telemetry-row">
                <span className="sidebar-telemetry-label">SIF Precursors:</span>
                <span className="sidebar-telemetry-val" style={{ color: 'var(--critical-red)' }}>
                  {kpis.summary.sif_precursors} ({kpis.summary.sif_rate}%)
                </span>
              </div>
              <div className="sidebar-telemetry-row">
                <span className="sidebar-telemetry-label">Active Actions:</span>
                <span className="sidebar-telemetry-val" style={{ color: 'var(--safety-amber)' }}>
                  {kpis.summary.in_progress_actions + kpis.summary.pending_verification}
                </span>
              </div>
              <div className="sidebar-telemetry-row">
                <span className="sidebar-telemetry-label">Verified Rate:</span>
                <span className="sidebar-telemetry-val" style={{ color: 'var(--verified-green)' }}>
                  {kpis.summary.verification_rate}%
                </span>
              </div>
            </div>
          )}
        </aside>

        {/* Central Workspace */}
        <main className="workstation-main">
        {/* Leading Indicators KPI Banner */}
        {kpis && (
          <section className="kpi-grid">
            <div className="glass-panel kpi-card">
              <div className="kpi-label">Total Ingested Reports</div>
              <div className="kpi-value">{kpis.summary.total_reports}</div>
              <div className="kpi-subtext">Multi-source incident observations</div>
            </div>

            <div className="glass-panel kpi-card critical">
              <div className="kpi-label">SIF Precursors Detected</div>
              <div className="kpi-value" style={{ color: 'var(--sif-critical)' }}>
                {kpis.summary.sif_precursors}
                <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>
                  ({kpis.summary.sif_rate}%)
                </span>
              </div>
              <div className="kpi-subtext">High-energy + compromised barriers</div>
            </div>

            <div className="glass-panel kpi-card warning">
              <div className="kpi-label">Active Corrective Actions</div>
              <div className="kpi-value" style={{ color: 'var(--sif-high)' }}>
                {kpis.summary.in_progress_actions + kpis.summary.pending_verification}
              </div>
              <div className="kpi-subtext">{kpis.summary.pending_verification} awaiting independent verification</div>
            </div>

            <div className="glass-panel kpi-card success">
              <div className="kpi-label">Verified Effective Rate</div>
              <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
                {kpis.summary.verification_rate}%
              </div>
              <div className="kpi-subtext">Closed only with documented physical proof</div>
            </div>
          </section>
        )}

        {/* TAB 1: TRIAGE & INCIDENT QUEUE (DUAL-PANE WORKSTATION) */}
        {activeTab === 'queue' && (
          <div className="queue-dual-pane">
            {/* Left Column: Filter Bar + Compact Technical Data Table */}
            <div>
              <div className="filter-bar">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 200 }}>
                  <Search size={14} style={{ color: 'var(--text-dim)' }} />
                  <input
                    type="text"
                    placeholder="Filter incidents, equipment, hazards..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-control"
                    id="search-input"
                  />
                </div>

                <select
                  className="input-control"
                  style={{ width: 145 }}
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  id="filter-priority-select"
                >
                  <option value="">All Priorities</option>
                  <option value="CRITICAL_SIF">CRITICAL SIF</option>
                  <option value="HIGH_PRECURSOR">HIGH PRECURSOR</option>
                  <option value="MEDIUM_RISK">MEDIUM RISK</option>
                  <option value="LOW_ROUTINE">LOW ROUTINE</option>
                </select>

                <select
                  className="input-control"
                  style={{ width: 175 }}
                  value={filterFacility}
                  onChange={(e) => setFilterFacility(e.target.value)}
                  id="filter-facility-select"
                >
                  <option value="">All Facilities</option>
                  <option value="Gulf Coast Refinery">Gulf Coast Refinery</option>
                  <option value="Rotterdam Chemical Complex">Rotterdam Chemical Complex</option>
                  <option value="Midwest Heavy Manufacturing">Midwest Heavy Manufacturing</option>
                  <option value="Great Lakes Logistics Center">Great Lakes Logistics Center</option>
                  <option value="Texas Petrochemical Hub">Texas Petrochemical Hub</option>
                </select>

                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  <input
                    type="checkbox"
                    checked={sifOnly}
                    onChange={(e) => setSifOnly(e.target.checked)}
                    id="sif-only-checkbox"
                  />
                  <span style={{ color: 'var(--critical-red)', fontWeight: 600 }}>SIF Only</span>
                </label>
              </div>

              {/* Technical Workstation Incident Table */}
              <div className="table-container">
                {filteredReports.length === 0 ? (
                  <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    No incident reports match the active filters.
                  </div>
                ) : (
                  <table className="industrial-table">
                    <thead>
                      <tr>
                        <th style={{ width: 120 }}>Priority</th>
                        <th style={{ width: 110 }}>Report UID</th>
                        <th>Facility & Area</th>
                        <th>High-Energy Hazard</th>
                        <th>Critical Barrier</th>
                        <th>Outcome</th>
                        <th style={{ textAlign: 'right', width: 130 }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredReports.map((report) => {
                        const isSelected = selectedReport && selectedReport.id === report.id;
                        return (
                          <tr
                            key={report.id}
                            className={isSelected ? 'selected' : ''}
                            onClick={() => setSelectedReport(report)}
                            id={`report-item-${report.id}`}
                          >
                            <td>
                              <span
                                className={`badge ${
                                  report.risk_priority === 'CRITICAL_SIF'
                                    ? 'badge-critical'
                                    : report.risk_priority === 'HIGH_PRECURSOR'
                                    ? 'badge-high'
                                    : report.risk_priority === 'MEDIUM_RISK'
                                    ? 'badge-medium'
                                    : 'badge-routine'
                                }`}
                              >
                                {report.sif_precursor_flag ? 'SIF ' : ''}
                                {report.risk_priority.replace('_', ' ')}
                              </span>
                            </td>
                            <td>
                              <span className="font-mono" style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.75rem' }}>
                                {report.report_uid}
                              </span>
                              <div style={{ fontSize: '0.675rem', color: 'var(--text-muted)' }}>{report.report_date}</div>
                            </td>
                            <td>
                              <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{report.facility}</div>
                              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{report.unit_or_area}</div>
                            </td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <Zap size={11} style={{ color: 'var(--safety-amber)' }} />
                                <span style={{ color: 'var(--text-secondary)' }}>{report.energy_source}</span>
                              </div>
                            </td>
                            <td>
                              <span
                                className="badge"
                                style={{
                                  color:
                                    report.barrier_status === 'Failed' || report.barrier_status === 'Bypassed'
                                      ? 'var(--critical-red)'
                                      : 'var(--text-secondary)'
                                }}
                              >
                                {report.barrier_status} ({report.barrier_name})
                              </span>
                            </td>
                            <td>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{report.actual_outcome}</div>
                            </td>
                            <td style={{ textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', gap: 4 }}>
                                <button
                                  className="btn btn-secondary"
                                  style={{ padding: '3px 7px', fontSize: '0.7rem' }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openActionModal(report);
                                  }}
                                  id={`add-action-btn-${report.id}`}
                                  title="Assign Corrective Action"
                                >
                                  <PlusCircle size={11} />
                                  <span>Action</span>
                                </button>
                                <button
                                  className="btn btn-secondary"
                                  style={{ padding: '3px 7px', fontSize: '0.7rem' }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedReport(report);
                                    setActiveTab('inspector');
                                  }}
                                  title="Open SIF Inspector"
                                >
                                  <Eye size={11} />
                                  <span>Inspect</span>
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>

            {/* Right Column: Dedicated Incident Inspection & Evidence Panel */}
            <div className="inspection-panel">
              {(() => {
                const activeRep = selectedReport || (filteredReports.length > 0 ? filteredReports[0] : null);
                if (!activeRep) {
                  return (
                    <div style={{ padding: 28, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      Select an incident from the queue to view full barrier telemetry and cited evidence.
                    </div>
                  );
                }

                let hist = null;
                try {
                  hist = typeof activeRep.historical_reference === 'string'
                    ? JSON.parse(activeRep.historical_reference)
                    : activeRep.historical_reference;
                } catch (e) {
                  hist = null;
                }

                return (
                  <div>
                    <div className="panel-header-section">
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                          <span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.875rem' }}>
                            {activeRep.report_uid}
                          </span>
                          <span
                            className={`badge ${
                              activeRep.risk_priority === 'CRITICAL_SIF'
                                ? 'badge-critical'
                                : activeRep.risk_priority === 'HIGH_PRECURSOR'
                                ? 'badge-high'
                                : activeRep.risk_priority === 'MEDIUM_RISK'
                                ? 'badge-medium'
                                : 'badge-routine'
                            }`}
                          >
                            {activeRep.risk_priority.replace('_', ' ')}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {activeRep.facility} • {activeRep.unit_or_area} • {activeRep.report_date}
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn btn-primary"
                          style={{ padding: '3px 8px', fontSize: '0.725rem' }}
                          onClick={() => openActionModal(activeRep)}
                        >
                          <PlusCircle size={11} />
                          <span>Action</span>
                        </button>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '0.725rem' }}
                          onClick={() => {
                            setSelectedReport(activeRep);
                            setActiveTab('inspector');
                          }}
                        >
                          <Eye size={11} />
                          <span>Full View</span>
                        </button>
                      </div>
                    </div>

                    {/* Incident Narrative Preview */}
                    <div style={{ marginBottom: 10 }}>
                      <div className="panel-section-title">Incident Observation</div>
                      <p style={{ fontSize: '0.775rem', color: 'var(--text-main)', lineHeight: 1.45, background: 'var(--bg-input)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-divider)' }}>
                        {activeRep.description}
                      </p>
                    </div>

                    {/* Actual vs Potential Outcome */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 10 }}>
                      <div style={{ background: 'var(--bg-panel-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-divider)' }}>
                        <div className="panel-section-title">Actual Outcome</div>
                        <div style={{ fontWeight: 700, fontSize: '0.8rem', color: 'var(--text-main)' }}>
                          {activeRep.actual_outcome}
                        </div>
                      </div>

                      <div style={{ background: 'var(--bg-panel-secondary)', padding: '6px 8px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-divider)' }}>
                        <div className="panel-section-title">Potential Consequence</div>
                        <div
                          style={{
                            fontWeight: 700,
                            fontSize: '0.8rem',
                            color: activeRep.potential_severity.includes('Critical') ? 'var(--critical-red)' : 'var(--text-main)'
                          }}
                        >
                          {activeRep.potential_severity}
                        </div>
                      </div>
                    </div>

                    {/* Precursor Detection Confidence Score Indicator */}
                    <PrecursorConfidenceIndicator report={activeRep} compact={true} />

                    {/* High-Energy & Barrier Analysis */}
                    <div style={{ background: 'var(--bg-panel-secondary)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', border: '1px solid var(--border-divider)', marginBottom: 10 }}>
                      <div className="panel-section-title">Barrier Breakdown</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, fontSize: '0.75rem' }}>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Hazard: </span>
                          <strong style={{ color: 'var(--text-main)' }}>{activeRep.energy_source}</strong>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Primary: </span>
                          <span
                            className="badge"
                            style={{
                              color:
                                activeRep.barrier_status === 'Failed' || activeRep.barrier_status === 'Bypassed'
                                  ? 'var(--critical-red)'
                                  : 'var(--verified-green)'
                            }}
                          >
                            {activeRep.barrier_status} ({activeRep.barrier_name})
                          </span>
                        </div>
                        {activeRep.secondary_barriers && activeRep.secondary_barriers.length > 0 && (
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Secondary: </span>
                            <div style={{ marginTop: 3, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                              {activeRep.secondary_barriers.map((sb, idx) => (
                                <span key={idx} className="badge badge-high" style={{ fontSize: '0.675rem' }}>
                                  {sb.status} ({sb.name})
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Cited Evidence Quotes */}
                    <div style={{ marginBottom: 10 }}>
                      <div className="panel-section-title">Cited Verbatim Evidence</div>
                      {JSON.parse(activeRep.evidence_snippets || '[]').map((snippet, idx) => (
                        <div key={idx} className="evidence-quote">
                          "{snippet}"
                        </div>
                      ))}
                    </div>

                    {/* Historical OSHA Reference */}
                    {hist && hist.matched && (
                      <div style={{ background: 'var(--bg-panel-secondary)', border: '1px solid var(--border-divider)', padding: '8px 10px', borderRadius: 'var(--radius-xs)', fontSize: '0.725rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                          <span className="badge badge-high">{hist.reference_record_id}</span>
                          <span style={{ fontFamily: 'monospace', color: 'var(--safety-amber)', fontWeight: 700 }}>
                            {hist.relevance_score}% Mechanism Match
                          </span>
                        </div>
                        <div style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>
                          <strong>{hist.location || hist.company_name}</strong> ({hist.fiscal_year})
                        </div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.675rem', lineHeight: 1.35, borderTop: '1px solid var(--border-divider)', paddingTop: 4 }}>
                          ℹ️ {hist.disclaimer}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* TAB 2: REPORT INGESTION HUB */}
        {activeTab === 'ingest' && (
          <div className="grid-2col">
            {/* Batch Upload Form */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <UploadCloud size={24} style={{ color: 'var(--accent-cyan)' }} />
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Batch File Upload (CSV / Excel)</h2>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20 }}>
                Upload workplace safety logs, near-miss sheets, or hazard inspection workbooks. Flexible column matching automatically extracts narratives, facilities, and dates.
              </p>

              <div
                style={{
                  border: '2px dashed var(--border-medium)',
                  borderRadius: 'var(--radius-md)',
                  padding: 36,
                  textAlign: 'center',
                  background: 'rgba(0,0,0,0.2)',
                  marginBottom: 20
                }}
              >
                <UploadCloud size={40} style={{ color: 'var(--accent-cyan)', marginBottom: 12 }} />
                <p style={{ fontSize: '0.9rem', marginBottom: 12 }}>Select a .csv or .xlsx safety file to ingest</p>
                <input
                  type="file"
                  accept=".csv, .xlsx, .xls"
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                  id="batch-file-input"
                />
                <label htmlFor="batch-file-input" className="btn btn-primary" style={{ cursor: 'pointer' }}>
                  Choose File & Ingest
                </label>
              </div>

              <div style={{ background: 'rgba(255,255,255,0.03)', padding: 14, borderRadius: 8, fontSize: '0.8rem' }}>
                <strong style={{ color: 'var(--accent-cyan)' }}>Supported Column Synonyms:</strong>
                <ul style={{ marginTop: 6, marginLeft: 16, color: 'var(--text-muted)' }}>
                  <li>Narrative: <code>description</code>, <code>narrative</code>, <code>details</code>, <code>incident_details</code></li>
                  <li>Facility: <code>facility</code>, <code>plant</code>, <code>site</code>, <code>location</code></li>
                  <li>Outcome: <code>actual_outcome</code>, <code>outcome</code>, <code>consequence</code></li>
                </ul>
              </div>
            </div>

            {/* Manual Structured Form */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <PlusCircle size={24} style={{ color: 'var(--accent-emerald)' }} />
                <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Structured Safety Report Entry</h2>
              </div>

              <form onSubmit={handleCreateReport} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Facility</label>
                    <input
                      type="text"
                      className="input-control"
                      value={newReport.facility}
                      onChange={(e) => setNewReport({ ...newReport, facility: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Unit / Plant Area</label>
                    <input
                      type="text"
                      className="input-control"
                      value={newReport.unit_or_area}
                      onChange={(e) => setNewReport({ ...newReport, unit_or_area: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Report Date</label>
                    <input
                      type="date"
                      className="input-control"
                      value={newReport.report_date}
                      onChange={(e) => setNewReport({ ...newReport, report_date: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Observation Type</label>
                    <select
                      className="input-control"
                      value={newReport.incident_type}
                      onChange={(e) => setNewReport({ ...newReport, incident_type: e.target.value })}
                    >
                      <option value="near_miss">Near Miss</option>
                      <option value="unsafe_condition">Unsafe Condition</option>
                      <option value="unsafe_act">Unsafe Act</option>
                      <option value="minor_injury">Minor First Aid</option>
                      <option value="property_damage">Property Damage</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>Actual Logged Outcome</label>
                  <input
                    type="text"
                    className="input-control"
                    value={newReport.actual_outcome}
                    onChange={(e) => setNewReport({ ...newReport, actual_outcome: e.target.value })}
                    placeholder="e.g. Near Miss (No Physical Harm), First Aid..."
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 4, display: 'block' }}>
                    Incident Narrative / Observation Details
                  </label>
                  <textarea
                    rows={4}
                    className="input-control"
                    value={newReport.description}
                    onChange={(e) => setNewReport({ ...newReport, description: e.target.value })}
                    placeholder="Describe what occurred, equipment involved, working at height, electrical state, or barrier failures..."
                    required
                    id="manual-report-description"
                  />
                </div>

                {/* Live AI Preview Box */}
                {livePreview && (
                  <div
                    style={{
                      background: 'rgba(0, 229, 255, 0.05)',
                      border: '1px solid var(--border-glow)',
                      padding: 12,
                      borderRadius: 8,
                      fontSize: '0.8rem'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>⚡ Live AI Triage Preview:</span>
                      <span
                        className={`badge ${
                          livePreview.risk_priority === 'CRITICAL_SIF'
                            ? 'badge-critical'
                            : livePreview.risk_priority === 'HIGH_PRECURSOR'
                            ? 'badge-high'
                            : 'badge-routine'
                        }`}
                      >
                        {livePreview.risk_priority}
                      </span>
                    </div>
                    <div style={{ color: 'var(--text-muted)' }}>
                      <strong>Energy:</strong> {livePreview.energy_source} | <strong>Primary Barrier:</strong> {livePreview.barrier_status} ({livePreview.barrier_name})
                      {livePreview.secondary_barriers && livePreview.secondary_barriers.length > 0 && (
                        <span style={{ color: 'var(--accent-amber)', marginLeft: 6 }}>
                          | <strong>Secondary:</strong> {livePreview.secondary_barriers.map(b => `${b.status} (${b.name})`).join(', ')}
                        </span>
                      )}
                    </div>
                    {livePreview.historical_reference?.matched && (
                      <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px dashed rgba(245, 158, 11, 0.3)', fontSize: '0.75rem', color: 'var(--accent-amber)' }}>
                        🏛️ <strong>OSHA Fatal Precedent:</strong> {livePreview.historical_reference.reference_record_id} ({livePreview.historical_reference.fiscal_year}) — {livePreview.historical_reference.relevance_score}% alignment
                      </div>
                    )}
                    <PrecursorConfidenceIndicator report={livePreview} compact={true} />
                  </div>
                )}

                <button type="submit" className="btn btn-primary" style={{ marginTop: 8 }} id="submit-manual-report-btn">
                  Submit & Triage Safety Report
                </button>
              </form>
            </div>
          </div>
        )}

        {/* TAB 3: SIF PRECURSOR & EVIDENCE INSPECTOR */}
        {activeTab === 'inspector' && selectedReport && (
          <div className="grid-2col">
            {/* Detailed Inspection */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <span className="font-mono" style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                    {selectedReport.report_uid}
                  </span>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>SIF Precursor Analysis</h2>
                </div>
                <span
                  className={`badge ${
                    selectedReport.risk_priority === 'CRITICAL_SIF'
                      ? 'badge-critical'
                      : selectedReport.risk_priority === 'HIGH_PRECURSOR'
                      ? 'badge-high'
                      : selectedReport.risk_priority === 'MEDIUM_RISK'
                      ? 'badge-medium'
                      : 'badge-routine'
                  }`}
                >
                  {selectedReport.risk_priority.replace('_', ' ')}
                </span>
              </div>

              {/* Risk Evaluation Summary */}
              <div
                style={{
                  background:
                    selectedReport.sif_precursor_flag
                      ? 'rgba(255, 51, 102, 0.08)'
                      : 'rgba(255, 255, 255, 0.03)',
                  border: `1px solid ${
                    selectedReport.sif_precursor_flag ? 'rgba(255, 51, 102, 0.3)' : 'var(--border-subtle)'
                  }`,
                  padding: 16,
                  borderRadius: 8,
                  marginBottom: 16
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: selectedReport.sif_precursor_flag ? 'var(--sif-critical)' : 'var(--accent-cyan)' }}>
                    {selectedReport.sif_precursor_flag ? '⚠️ High-Energy SIF Precursor Confirmed' : 'ℹ️ Risk Evaluation Summary'}
                  </div>
                  <span
                    className={`badge ${
                      selectedReport.risk_priority === 'CRITICAL_SIF'
                        ? 'badge-critical'
                        : selectedReport.risk_priority === 'HIGH_PRECURSOR'
                        ? 'badge-high'
                        : selectedReport.risk_priority === 'MEDIUM_RISK'
                        ? 'badge-medium'
                        : 'badge-routine'
                    }`}
                    style={{ fontSize: '0.7rem' }}
                  >
                    {selectedReport.risk_priority.replace('_', ' ')}
                  </span>
                </div>
                <p style={{ fontSize: '0.875rem', lineHeight: 1.65, color: 'var(--text-main)', marginBottom: 0 }}>
                  {selectedReport.explanation}
                </p>
              </div>

              {/* Precursor Detection Confidence Indicator */}
              <PrecursorConfidenceIndicator report={selectedReport} compact={false} />

              {/* Distinguishing Actual Outcome vs Potential Consequence */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 16,
                  padding: 16,
                  background: 'rgba(0,0,0,0.25)',
                  borderRadius: 8,
                  marginBottom: 20
                }}
              >
                <div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Actual Event Outcome</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4 }}>{selectedReport.actual_outcome}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>What happened to the worker physically</div>
                </div>

                <div>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Potential Consequence</div>
                  <div
                    style={{
                      fontSize: '1rem',
                      fontWeight: 800,
                      marginTop: 4,
                      color: selectedReport.potential_severity.includes('Critical') ? 'var(--sif-critical)' : 'var(--accent-cyan)'
                    }}
                  >
                    {selectedReport.potential_severity}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>Maximum credible outcome without luck</div>
                </div>
              </div>

              {/* Extracted Dimensions */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                <div style={{ background: 'rgba(255,255,255,0.02)', padding: 12, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>High-Energy Category</div>
                  <div style={{ fontWeight: 600, color: 'var(--accent-cyan)', marginTop: 2 }}>{selectedReport.energy_source}</div>
                </div>

                <div style={{ background: 'rgba(255,255,255,0.02)', padding: 12, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>Critical Barrier State</div>
                  <div style={{ fontWeight: 600, color: 'var(--sif-high)', marginTop: 2 }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: 4, fontWeight: 700 }}>Primary:</span>
                    {selectedReport.barrier_status} ({selectedReport.barrier_name})
                  </div>
                  {selectedReport.secondary_barriers && selectedReport.secondary_barriers.length > 0 && (
                    <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                      {selectedReport.secondary_barriers.map((sb, idx) => (
                        <span key={idx} className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-amber)', fontSize: '0.7rem' }}>
                          Secondary: {sb.status} ({sb.name})
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Cited Evidence (Zero Hallucination Guarantee) */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8 }}>
                  Cited Evidence Snippets from Raw Report (Auditable Zero-Hallucination)
                </div>
                {JSON.parse(selectedReport.evidence_snippets || '[]').map((snippet, idx) => (
                  <div key={idx} className="evidence-quote">
                    "{snippet}"
                  </div>
                ))}
              </div>

              {/* Historical OSHA Fatal-Incident Mechanism Reference (Empirical Registry) */}
              {(() => {
                let hist = null;
                try {
                  hist = typeof selectedReport.historical_reference === 'string'
                    ? JSON.parse(selectedReport.historical_reference)
                    : selectedReport.historical_reference;
                } catch (e) {
                  hist = null;
                }

                return (
                  <div style={{ marginBottom: 24 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <BookOpen size={14} style={{ color: 'var(--accent-amber)' }} />
                      <span>Historical OSHA Fatal-Incident References</span>
                    </div>

                    {hist && hist.matched ? (
                      <div style={{
                        background: 'rgba(245, 158, 11, 0.05)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        borderRadius: 8,
                        padding: 16
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.2)', color: 'var(--accent-amber)', fontWeight: 700 }}>
                              {hist.reference_record_id}
                            </span>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                              {hist.fiscal_year} • File: <code>{hist.source_file}</code>
                            </span>
                          </div>
                          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
                            ⚡ {hist.relevance_score}% Mechanism Alignment
                          </div>
                        </div>

                        <div style={{ fontSize: '0.85rem', marginBottom: 8, color: 'var(--text-normal)' }}>
                          <strong style={{ color: 'var(--text-muted)' }}>Location / Employer:</strong> {hist.location || hist.company_name}
                        </div>

                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginBottom: 4, textTransform: 'uppercase', fontWeight: 600 }}>
                            Original Fatal Investigation Narrative:
                          </div>
                          <div style={{
                            background: 'rgba(0, 0, 0, 0.35)',
                            padding: '10px 14px',
                            borderRadius: 6,
                            fontSize: '0.85rem',
                            lineHeight: 1.5,
                            color: '#fef3c7',
                            borderLeft: '3px solid var(--accent-amber)'
                          }}>
                            "{hist.original_narrative}"
                          </div>
                        </div>

                        <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: 10, lineHeight: 1.5 }}>
                          <strong style={{ color: 'var(--accent-cyan)' }}>Why Relevant: </strong>
                          {hist.relevance_rationale}
                        </div>

                        <div style={{
                          fontSize: '0.725rem',
                          color: 'var(--text-dim)',
                          borderTop: '1px solid rgba(255,255,255,0.08)',
                          paddingTop: 8,
                          fontStyle: 'italic'
                        }}>
                          ℹ️ {hist.disclaimer}
                        </div>
                      </div>
                    ) : (
                      <div style={{
                        background: 'rgba(255, 255, 255, 0.02)',
                        border: '1px dashed var(--border-subtle)',
                        borderRadius: 8,
                        padding: 14,
                        fontSize: '0.825rem',
                        color: 'var(--text-dim)'
                      }}>
                        {hist?.relevance_rationale || 'No relevant historical OSHA reference found.'}
                      </div>
                    )}
                  </div>
                );
              })()}

              <div style={{ display: 'flex', gap: 12 }}>
                <button className="btn btn-primary" onClick={() => openActionModal(selectedReport)}>
                  <PlusCircle size={15} />
                  <span>Assign Corrective Action</span>
                </button>
              </div>
            </div>

            {/* Recurrence & Cross-Site Matches */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <Layers size={20} style={{ color: 'var(--accent-purple)' }} />
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Semantically Similar Incidents Across Sites</h3>
              </div>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: 16 }}>
                Identifies previous barrier failures matching this hazard pattern, even if described using different terminology.
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {similarIncidents.length === 0 ? (
                  <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                    No recurring incidents matched above the similarity threshold.
                  </div>
                ) : (
                  similarIncidents.map((sim) => (
                    <div
                      key={sim.id}
                      style={{
                        background: 'rgba(255,255,255,0.03)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 8,
                        padding: 14
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span
                            className="badge"
                            style={{
                              background: sim.is_cross_site ? 'rgba(139, 92, 246, 0.15)' : 'rgba(0, 229, 255, 0.15)',
                              color: sim.is_cross_site ? 'var(--accent-purple)' : 'var(--accent-cyan)'
                            }}
                          >
                            {sim.recurrence_type}
                          </span>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{sim.facility}</span>
                        </div>
                        <span className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                          {sim.similarity_score}% match
                        </span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: 8 }}>{sim.description}</p>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Date: {sim.report_date} | Energy: {sim.energy_source} | Barrier: {sim.barrier_status}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: HIERARCHY OF CONTROLS & VERIFICATION GATE */}
        {activeTab === 'actions' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Corrective-Action Tracking & Verification Gates</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Enforcing the Hierarchy of Controls and preventing false closure through required evidence verification.
                </p>
              </div>
            </div>

            <div className="reports-list">
              {actions.length === 0 ? (
                <div className="glass-panel" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                  No corrective actions have been assigned yet. Select a report from the Incident Queue to create one.
                </div>
              ) : (
                actions.map((act) => {
                  const isVerified = act.status === 'Verified & Closed';
                  return (
                    <div key={act.id} className="glass-panel" style={{ padding: 20 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                            <span className="font-mono" style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                              {act.action_uid}
                            </span>
                            <span
                              className="badge"
                              style={{
                                background:
                                  act.hierarchy_level === 'Elimination' || act.hierarchy_level === 'Engineering Controls'
                                    ? 'rgba(0, 229, 255, 0.15)'
                                    : 'rgba(245, 158, 11, 0.15)',
                                color:
                                  act.hierarchy_level === 'Elimination' || act.hierarchy_level === 'Engineering Controls'
                                    ? 'var(--accent-cyan)'
                                    : 'var(--accent-amber)'
                              }}
                            >
                              {act.hierarchy_level}
                            </span>
                            <span className={`badge ${isVerified ? 'badge-verified' : 'badge-high'}`}>
                              {act.status}
                            </span>
                          </div>
                          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>{act.title}</h3>
                        </div>

                        {!isVerified && (
                          <button
                            className="btn btn-success"
                            style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                            onClick={() => openVerifyModal(act)}
                            id={`verify-action-btn-${act.id}`}
                          >
                            <ShieldAlert size={14} />
                            <span>Verify & Close Gate</span>
                          </button>
                        )}
                      </div>

                      <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: 14 }}>
                        {act.description}
                      </p>

                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          borderTop: '1px solid var(--border-subtle)',
                          paddingTop: 12,
                          fontSize: '0.775rem',
                          color: 'var(--text-dim)'
                        }}
                      >
                        <div>
                          <span>Assignee: </span>
                          <strong style={{ color: 'var(--text-main)' }}>{act.owner_name}</strong> ({act.owner_department})
                          <span style={{ margin: '0 8px' }}>•</span>
                          <span>Target Date: </span>
                          <strong style={{ color: 'var(--text-main)' }}>{act.target_date}</strong>
                        </div>

                        {isVerified && (
                          <div style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                            ✓ Verified by: {act.verified_by} | Evidence: "{act.verification_notes}"
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* TAB 5: RECURRENCE & CROSS-SITE LEARNING */}
        {activeTab === 'recurrence' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Cross-Site Learning & Barrier Degradation Patterns</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Aggregating recurring hazard vulnerabilities across brother/sister plants to eliminate siloed learning.
              </p>
            </div>

            {crossSiteData && (
              <div className="grid-2col">
                {/* Top Compromised Barriers */}
                <div className="glass-panel" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>
                    Top Compromised Safety Barriers
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {crossSiteData.top_compromised_barriers.map((b, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: 12,
                          background: 'rgba(255,255,255,0.02)',
                          borderRadius: 8
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{b.barrier}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Reported across multiple sites</div>
                        </div>
                        <span className="badge badge-critical" style={{ fontSize: '0.85rem' }}>
                          {b.count} failures
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SIF Rate by Facility */}
                <div className="glass-panel" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>
                    Facility Precursor Distribution
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {crossSiteData.site_risk_distribution.map((site, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: 12,
                          background: 'rgba(255,255,255,0.02)',
                          borderRadius: 8
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{site.facility}</span>
                          <span style={{ fontSize: '0.8rem', color: 'var(--sif-critical)', fontWeight: 700 }}>
                            {site.sif_precursors} Precursors / {site.total_reports} Reports
                          </span>
                        </div>
                        <div
                          style={{
                            height: 6,
                            background: 'rgba(255,255,255,0.1)',
                            borderRadius: 3,
                            overflow: 'hidden'
                          }}
                        >
                          <div
                            style={{
                              width: `${Math.min(100, (site.sif_precursors / (site.total_reports || 1)) * 100)}%`,
                              height: '100%',
                              background: 'var(--sif-critical)'
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 6: MANAGEMENT ANALYTICS */}
        {activeTab === 'analytics' && kpis && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Executive Industrial Safety Analytics</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Auditable leading safety metrics. Every statistic connects directly to verified records.
              </p>
            </div>

            <div className="grid-2col">
              {/* Energy Source Distribution */}
              <div className="glass-panel" style={{ padding: 24 }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>High-Energy Hazards Identified</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {kpis.energy_sources.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: 8, background: 'rgba(255,255,255,0.02)', borderRadius: 6 }}>
                      <span style={{ fontSize: '0.85rem' }}>{item.energy}</span>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Facility Comparison */}
              <div className="glass-panel" style={{ padding: 24 }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 16 }}>Site Risk Benchmark Comparison</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-medium)', textAlign: 'left', color: 'var(--text-dim)' }}>
                      <th style={{ padding: '8px 0' }}>Facility</th>
                      <th>Total Reports</th>
                      <th>SIF Precursors</th>
                      <th>SIF Ratio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {kpis.facilities.map((f, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 0', fontWeight: 600 }}>{f.facility}</td>
                        <td>{f.total_reports}</td>
                        <td style={{ color: 'var(--sif-critical)', fontWeight: 700 }}>{f.sif_precursors}</td>
                        <td style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>{f.sif_ratio}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 7: BENCHMARK EVALUATION */}
        {activeTab === 'benchmark' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Model Benchmark & Evaluation Transparency</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Transparent evaluation against Campbell Institute & OSHA benchmark cases. Zero false claims.
                </p>
              </div>
              <button className="btn btn-primary" onClick={handleSeedBenchmark} id="re-seed-benchmark-btn">
                <RefreshCw size={14} />
                <span>Re-Seed Benchmark Data</span>
              </button>
            </div>

            {benchmarkEvaluation && (
              <div>
                {/* Metrics Cards */}
                <div className="kpi-grid">
                  <div className="glass-panel kpi-card">
                    <div className="kpi-label">Benchmark Accuracy</div>
                    <div className="kpi-value" style={{ color: 'var(--accent-cyan)' }}>
                      {benchmarkEvaluation.metrics.accuracy}%
                    </div>
                  </div>
                  <div className="glass-panel kpi-card">
                    <div className="kpi-label">Precision (SIF Precursors)</div>
                    <div className="kpi-value" style={{ color: 'var(--accent-emerald)' }}>
                      {benchmarkEvaluation.metrics.precision}%
                    </div>
                  </div>
                  <div className="glass-panel kpi-card">
                    <div className="kpi-label">Recall (SIF Precursors)</div>
                    <div className="kpi-value" style={{ color: 'var(--sif-critical)' }}>
                      {benchmarkEvaluation.metrics.recall}%
                    </div>
                  </div>
                  <div className="glass-panel kpi-card">
                    <div className="kpi-label">F1-Score</div>
                    <div className="kpi-value" style={{ color: 'var(--accent-purple)' }}>
                      {benchmarkEvaluation.metrics.f1_score}%
                    </div>
                  </div>
                </div>

                {/* Confusion Matrix */}
                <div className="glass-panel" style={{ padding: 24, marginBottom: 24 }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 12 }}>Confusion Matrix (Evaluated Records)</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, textAlign: 'center' }}>
                    <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent-emerald)', padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                        {benchmarkEvaluation.confusion_matrix.true_positives}
                      </div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>True Positives</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Correctly flagged SIF</div>
                    </div>
                    <div style={{ background: 'rgba(255, 51, 102, 0.1)', border: '1px solid var(--sif-critical)', padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--sif-critical)' }}>
                        {benchmarkEvaluation.confusion_matrix.false_positives}
                      </div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>False Positives</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Non-SIF flagged as SIF</div>
                    </div>
                    <div style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid var(--sif-medium)', padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--sif-medium)' }}>
                        {benchmarkEvaluation.confusion_matrix.true_negatives}
                      </div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>True Negatives</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Correctly filtered routine</div>
                    </div>
                    <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid var(--accent-amber)', padding: 16, borderRadius: 8 }}>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-amber)' }}>
                        {benchmarkEvaluation.confusion_matrix.false_negatives}
                      </div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600 }}>False Negatives</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Missed SIF precursors</div>
                    </div>
                  </div>
                </div>

                {/* Case Evaluations */}
                <div className="glass-panel" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 14 }}>Individual Benchmark Case Results</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {benchmarkEvaluation.case_evaluations.map((c, idx) => (
                      <div key={idx} style={{ padding: 12, background: 'rgba(255,255,255,0.02)', borderRadius: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ flex: 1, marginRight: 16 }}>
                          <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{c.facility}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{c.description}</div>
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span className={`badge ${c.result_category === 'True Positive' ? 'badge-critical' : c.result_category === 'True Negative' ? 'badge-routine' : 'badge-high'}`}>
                            {c.result_category}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 8: AI SAFETY DOCUMENT INTELLIGENCE & EVIDENCE Q&A */}
        {activeTab === 'library' && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>AI Safety Document Intelligence & Evidence Q&A</h2>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    Evidence-grounded question answering and provenance retrieval across official safety investigation reports (IOCL Haldia, Tesoro Anacortes, Chevron Richmond).
                  </p>
                </div>
                {kbSummary && (
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <span className="badge" style={{ background: 'rgba(0, 229, 255, 0.1)', color: 'var(--accent-cyan)' }}>
                      {kbSummary.total_chunks} Chunks
                    </span>
                    <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-emerald)' }}>
                      {kbSummary.fact_type_breakdown.REPORTED_FACT || 0} Facts
                    </span>
                    <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.1)', color: 'var(--accent-amber)' }}>
                      {kbSummary.fact_type_breakdown.INVESTIGATOR_CONCLUSION || 0} Root Causes
                    </span>
                    <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.1)', color: 'var(--accent-purple)' }}>
                      {kbSummary.fact_type_breakdown.OFFICIAL_RECOMMENDATION || 0} Recommendations
                    </span>
                    <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--sif-critical)' }}>
                      {Object.keys(kbSummary.iogp_rules_breakdown || {}).length} IOGP Rules
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Sub-Navigation Modes */}
            <div className="sub-nav-tabs">
              <button
                type="button"
                className={`sub-nav-tab ${kbSubTab === 'qa' ? 'active' : ''}`}
                onClick={() => setKbSubTab('qa')}
                id="subtab-qa"
              >
                <BookOpen size={15} />
                <span>💬 Ask Documents (Evidence Q&A)</span>
              </button>
              <button
                type="button"
                className={`sub-nav-tab ${kbSubTab === 'search' ? 'active' : ''}`}
                onClick={() => setKbSubTab('search')}
                id="subtab-search"
              >
                <Search size={15} />
                <span>🔍 Evidence & Findings Explorer</span>
              </button>
              <button
                type="button"
                className={`sub-nav-tab ${kbSubTab === 'upload' ? 'active' : ''}`}
                onClick={() => setKbSubTab('upload')}
                id="subtab-upload"
              >
                <UploadCloud size={15} />
                <span>📤 Ingest Investigation Report (PDF)</span>
              </button>
            </div>

            {/* MODE 1: EVIDENCE-GROUNDED Q&A */}
            {kbSubTab === 'qa' && (
              <div>
                <div className="glass-panel" style={{ padding: 20, marginBottom: 20 }}>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleQaAsk();
                    }}
                    style={{ display: 'flex', gap: 12, marginBottom: 14 }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                      <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
                      <input
                        type="text"
                        className="input-control"
                        placeholder="Ask anything about hazards, safeguard failures, root causes, or recommendations in the reports..."
                        value={qaQuery}
                        onChange={(e) => setQaQuery(e.target.value)}
                        id="qa-search-input"
                      />
                    </div>
                    <select
                      className="input-control"
                      style={{ width: 220 }}
                      value={kbFilterReport}
                      onChange={(e) => setKbFilterReport(e.target.value)}
                      id="qa-filter-report"
                    >
                      <option value="">All Priority Reports</option>
                      <option value="Haldia">IOCL Haldia Refinery</option>
                      <option value="Tesoro">Tesoro Anacortes Refinery</option>
                      <option value="Chevron">Chevron Richmond Refinery</option>
                    </select>
                    <button type="submit" className="btn btn-primary" id="qa-search-btn" disabled={qaLoading}>
                      {qaLoading ? 'Analyzing Evidence...' : 'Ask Evidence Engine'}
                    </button>
                  </form>

                  {/* Pre-Built Inquiry Chips */}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 600 }}>Suggested Questions:</span>
                    {[
                      { label: 'IOCL Haldia: Naphtha fire & failed safeguards', q: 'What caused the naphtha fire at IOCL Haldia refinery and which safeguards failed?' },
                      { label: 'Tesoro Anacortes: Heat exchanger rupture & HTHA', q: 'Why did heat exchanger E-6600E rupture at Tesoro Anacortes and what was the role of HTHA?' },
                      { label: 'Chevron Richmond: Sulfidation corrosion & clamp intervention', q: 'What caused the pipe rupture at Chevron Richmond crude unit and why was sulfidation corrosion missed?' },
                      { label: 'Cross-Case: Hot work & energy isolation failures', q: 'What repeated failures in hot work and energy isolation appear across these reports?' }
                    ].map((item, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="chip-btn"
                        onClick={() => {
                          setQaQuery(item.q);
                          handleQaAsk(item.q);
                        }}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Q&A Result Container */}
                {qaLoading ? (
                  <div className="glass-panel" style={{ padding: 48, textAlign: 'center', color: 'var(--accent-cyan)' }}>
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <RefreshCw size={22} className="pulse-glow" />
                      <span style={{ fontSize: '1rem', fontWeight: 600 }}>Retrieving grounded evidence across investigation reports & page citations...</span>
                    </div>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Evaluating documented facts, checking physical barrier failures, and isolating AI inferences.
                    </p>
                  </div>
                ) : qaResult && (
                  <div className="glass-panel qa-card" id="qa-result-container">
                    {/* Header Bar */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: 14, marginBottom: 16 }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
                          <span className="badge badge-critical" style={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Evidence-Grounded Synthesis
                          </span>
                          {qaResult.reports_cited && qaResult.reports_cited.map((rep, idx) => (
                            <span key={idx} className="badge" style={{ background: 'rgba(0, 229, 255, 0.1)', color: 'var(--accent-cyan)' }}>
                              📄 {rep}
                            </span>
                          ))}
                        </div>
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>"{qaResult.query}"</h3>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span className="font-mono" style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                          {qaResult.top_match_score ? `${qaResult.top_match_score}% Confidence` : 'Evidence Cited'}
                        </span>
                      </div>
                    </div>

                    {/* Executive Summary */}
                    <div style={{ marginBottom: 18, lineHeight: 1.6, fontSize: '0.95rem', color: 'var(--text-main)' }}>
                      <strong>Executive Summary:</strong> {qaResult.executive_summary}
                    </div>

                    {/* Documented Facts with Page Citations */}
                    {qaResult.documented_facts && qaResult.documented_facts.length > 0 && (
                      <div className="qa-section-box">
                        <div className="qa-section-header" style={{ color: 'var(--accent-cyan)' }}>
                          <FileText size={16} />
                          <span>Documented Facts (Direct Page Citations)</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {qaResult.documented_facts.map((f, idx) => (
                            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, background: 'rgba(255,255,255,0.02)', padding: '8px 12px', borderRadius: 6 }}>
                              <span style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: 1.5 }}>
                                • {f.fact}
                              </span>
                              <span className="badge" style={{ background: 'rgba(0, 229, 255, 0.15)', color: 'var(--accent-cyan)', fontSize: '0.725rem', whiteSpace: 'nowrap' }}>
                                {f.citation}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Failed Safeguards & Contributing Factors */}
                    {((qaResult.failed_safeguards && qaResult.failed_safeguards.length > 0) || (qaResult.contributing_factors && qaResult.contributing_factors.length > 0)) && (
                      <div className="grid-2col" style={{ marginTop: 14 }}>
                        {qaResult.failed_safeguards && qaResult.failed_safeguards.length > 0 && (
                          <div className="qa-section-box" style={{ margin: 0 }}>
                            <div className="qa-section-header" style={{ color: 'var(--sif-critical)' }}>
                              <ShieldAlert size={16} />
                              <span>Failed Safety Barriers & Physical Breakdowns</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {qaResult.failed_safeguards.map((sg, idx) => (
                                <div key={idx} style={{ fontSize: '0.825rem', color: '#fca5a5' }}>
                                  <strong>⚠️ {sg.barrier}</strong>
                                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginTop: 2 }}>{sg.citation}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {qaResult.contributing_factors && qaResult.contributing_factors.length > 0 && (
                          <div className="qa-section-box" style={{ margin: 0 }}>
                            <div className="qa-section-header" style={{ color: 'var(--sif-high)' }}>
                              <AlertTriangle size={16} />
                              <span>Causal Factors & Organizational Deficiencies</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                              {qaResult.contributing_factors.map((cf, idx) => (
                                <div key={idx} style={{ fontSize: '0.825rem', color: '#fde047' }}>
                                  <strong>⚙️ {cf.factor}</strong>
                                  <div style={{ fontSize: '0.725rem', color: 'var(--text-dim)', marginTop: 2 }}>{cf.citation}</div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Implicated IOGP Life-Saving Rules */}
                    {qaResult.iogp_rules && qaResult.iogp_rules.length > 0 && (
                      <div className="qa-section-box">
                        <div className="qa-section-header" style={{ color: 'var(--accent-emerald)' }}>
                          <Zap size={16} />
                          <span>Implicated IOGP Life-Saving Rules</span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 10 }}>
                          {qaResult.iogp_rules.map((rule, idx) => (
                            <div key={idx} style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: 10, borderRadius: 6 }}>
                              <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--accent-emerald)', marginBottom: 2 }}>
                                🛡️ {rule.rule_name}: "{rule.directive}"
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {rule.description}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Official Recommendations */}
                    {qaResult.official_recommendations && qaResult.official_recommendations.length > 0 && (
                      <div className="qa-section-box">
                        <div className="qa-section-header" style={{ color: 'var(--accent-purple)' }}>
                          <CheckCircle size={16} />
                          <span>Official Investigator Recommendations</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {qaResult.official_recommendations.map((rec, idx) => (
                            <div key={idx} style={{ fontSize: '0.825rem', color: '#ddd6fe', lineHeight: 1.5 }}>
                              • {rec.text} <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.2)', color: '#c4b5fd', fontSize: '0.7rem' }}>{rec.citation}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* AI Interpretation Box (Explicitly Separated & Labeled) */}
                    {qaResult.ai_interpretation && (
                      <div className="ai-inference-box">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-purple)', fontWeight: 700, fontSize: '0.85rem', marginBottom: 6 }}>
                          <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.25)', color: '#c4b5fd' }}>
                            AI-GENERATED SYNTHESIS
                          </span>
                          <span>Pattern Interpretation (Requires Human Review)</span>
                        </div>
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                          {qaResult.ai_interpretation}
                        </p>
                      </div>
                    )}

                    {/* Missing / Uncertain Evidence Disclosures */}
                    {qaResult.missing_information && (
                      <div className="missing-info-box">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-amber)', fontWeight: 700, fontSize: '0.85rem', marginBottom: 6 }}>
                          <AlertTriangle size={15} />
                          <span>Missing or Uncertain Evidence Disclosures</span>
                        </div>
                        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                          {qaResult.missing_information}
                        </p>
                      </div>
                    )}

                    {/* Verbatim Evidence Citations Drawer */}
                    {qaResult.evidence_citations && qaResult.evidence_citations.length > 0 && (
                      <div style={{ marginTop: 20, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                            Source Citations & Verbatim Excerpts ({qaResult.evidence_citations.length})
                          </span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                          {qaResult.evidence_citations.map((c, idx) => (
                            <div key={idx} style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 6, padding: 12 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                  <span className="badge" style={{ background: 'rgba(0, 229, 255, 0.1)', color: 'var(--accent-cyan)' }}>
                                    {c.source_report}
                                  </span>
                                  <span className="badge" style={{ background: 'rgba(255,255,255,0.06)', color: '#fff' }}>
                                    Page {c.page_number}
                                  </span>
                                  <span className="badge badge-routine">
                                    {c.fact_type}
                                  </span>
                                </div>
                                <span className="font-mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                                  {c.match_score}% match
                                </span>
                              </div>
                              <div className="evidence-quote" style={{ fontSize: '0.825rem', color: '#cbd5e1' }}>
                                "{c.supporting_text}"
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* MODE 2: EVIDENCE & FINDINGS EXPLORER */}
            {kbSubTab === 'search' && (
              <div>
                <div className="glass-panel" style={{ padding: 20, marginBottom: 20 }}>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleKbSearch();
                    }}
                    style={{ display: 'flex', gap: 12, marginBottom: 14 }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
                      <Search size={18} style={{ color: 'var(--accent-cyan)' }} />
                      <input
                        type="text"
                        className="input-control"
                        placeholder="Search findings across reports (e.g. 'naphtha drain choke', 'HTHA Nelson curve', 'sulfidation corrosion')..."
                        value={kbQuery}
                        onChange={(e) => setKbQuery(e.target.value)}
                        id="kb-search-input"
                      />
                    </div>
                    <button type="submit" className="btn btn-primary" id="kb-search-btn">
                      {kbLoading ? 'Searching...' : 'Search Findings'}
                    </button>
                  </form>

                  {/* Filters */}
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <select
                      className="input-control"
                      style={{ width: 260 }}
                      value={kbFilterReport}
                      onChange={(e) => setKbFilterReport(e.target.value)}
                      id="kb-filter-report"
                    >
                      <option value="">All Investigation Reports</option>
                      <option value="Haldia">IOCL Haldia Refinery</option>
                      <option value="Tesoro">Tesoro Anacortes Refinery</option>
                      <option value="Chevron">Chevron Richmond Refinery</option>
                    </select>

                    <select
                      className="input-control"
                      style={{ width: 230 }}
                      value={kbFilterFactType}
                      onChange={(e) => setKbFilterFactType(e.target.value)}
                      id="kb-filter-fact-type"
                    >
                      <option value="">All Fact Types</option>
                      <option value="REPORTED_FACT">REPORTED_FACT (Direct Evidence)</option>
                      <option value="INVESTIGATOR_CONCLUSION">INVESTIGATOR_CONCLUSION (Root Causes)</option>
                      <option value="OFFICIAL_RECOMMENDATION">OFFICIAL_RECOMMENDATION</option>
                      <option value="KEY_LESSON">KEY_LESSON</option>
                    </select>

                    <select
                      className="input-control"
                      style={{ width: 220 }}
                      value={kbFilterIogp}
                      onChange={(e) => setKbFilterIogp(e.target.value)}
                      id="kb-filter-iogp"
                    >
                      <option value="">All IOGP Rules</option>
                      <option value="Hot Work">Hot Work</option>
                      <option value="Energy Isolation">Energy Isolation</option>
                      <option value="Bypassing Safety Controls">Bypassing Safety Controls</option>
                      <option value="Line of Fire">Line of Fire</option>
                      <option value="Work Authorisation">Work Authorisation</option>
                    </select>
                  </div>
                </div>

                {/* Search Results List */}
                <div className="reports-list">
                  {kbLoading ? (
                    <div className="glass-panel" style={{ padding: 40, textAlign: 'center', color: 'var(--accent-cyan)' }}>
                      Searching investigation reports with dense semantic vector embeddings...
                    </div>
                  ) : kbResults.length === 0 ? (
                    <div className="glass-panel" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                      No passages found matching the filter criteria.
                    </div>
                  ) : (
                    kbResults.map((res, idx) => (
                      <div key={idx} className="glass-panel" style={{ padding: 20 }} id={`kb-result-${idx}`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                            <span className="badge" style={{ background: 'rgba(0, 229, 255, 0.15)', color: 'var(--accent-cyan)', fontWeight: 700 }}>
                              📄 {res.source_report}
                            </span>
                            <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)', color: '#fff' }}>
                              Page {res.page_number}
                            </span>
                            <span
                              className={`badge ${
                                res.fact_type === 'REPORTED_FACT'
                                  ? 'badge-medium'
                                  : res.fact_type === 'INVESTIGATOR_CONCLUSION'
                                  ? 'badge-critical'
                                  : res.fact_type === 'OFFICIAL_RECOMMENDATION'
                                  ? 'badge-verified'
                                  : 'badge-high'
                              }`}
                            >
                              {res.fact_type}
                            </span>
                            <span className="badge" style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-dim)' }}>
                              Section: {res.section_type}
                            </span>
                          </div>
                          <span className="font-mono" style={{ fontSize: '0.85rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                            {res.score}% Match
                          </span>
                        </div>

                        <div style={{ display: 'flex', gap: 14, marginBottom: 12, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          <div>
                            <strong style={{ color: 'var(--text-dim)' }}>Incident:</strong> {res.incident}
                          </div>
                          {res.failed_safeguard !== 'Not explicitly stated' && (
                            <div>
                              <strong style={{ color: 'var(--sif-critical)' }}>Failed Barrier:</strong> {res.failed_safeguard}
                            </div>
                          )}
                        </div>

                        <div className="evidence-quote" style={{ fontSize: '0.9rem', marginBottom: 12, lineHeight: 1.6 }}>
                          "{res.supporting_text}"
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border-subtle)', paddingTop: 10, fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                          <div>
                            <span>File: <code>{res.pdf_filename}</code> (Page {res.page_number})</span>
                          </div>
                          <div style={{ display: 'flex', gap: 8 }}>
                            {res.iogp_rules && res.iogp_rules.map((r, rIdx) => (
                              <span key={rIdx} className="badge" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-emerald)' }}>
                                {r.rule_name}
                              </span>
                            ))}
                            <span className="badge badge-routine">
                              Triage: {res.ai_interpretation.risk_priority}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* MODE 3: INGEST INVESTIGATION REPORT (PDF) */}
            {kbSubTab === 'upload' && (
              <div className="glass-panel" style={{ padding: 28 }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 8, color: '#fff' }}>
                  Ingest New Investigation Report (PDF)
                </h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20 }}>
                  Upload a safety investigation report, incident inquiry report, or near-miss dossier. SAJAG extracts text page-by-page, classifies fact types, isolates failed safeguards, identifies IOGP Life-Saving Rules, and indexes vector embeddings into the auditable knowledge store.
                </p>

                <form onSubmit={handlePdfUpload} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div className="file-dropzone" onClick={() => document.getElementById('pdf-file-input').click()}>
                    <UploadCloud size={36} style={{ color: 'var(--accent-cyan)', marginBottom: 10 }} />
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#fff', marginBottom: 4 }}>
                      {pdfFile ? pdfFile.name : 'Click to select PDF Investigation Report'}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                      Supports standard PDF reports up to 50MB (Page citations preserved automatically)
                    </div>
                    <input
                      id="pdf-file-input"
                      type="file"
                      accept=".pdf"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          setPdfFile(e.target.files[0]);
                        }
                      }}
                    />
                  </div>

                  {pdfFile && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '10px 16px', borderRadius: 6 }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)' }}>
                        Selected: <strong>{pdfFile.name}</strong> ({(pdfFile.size / (1024 * 1024)).toFixed(2)} MB)
                      </span>
                      <button
                        type="button"
                        style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.8rem' }}
                        onClick={() => setPdfFile(null)}
                      >
                        Remove
                      </button>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={!pdfFile || uploadingPdf}
                      id="submit-pdf-upload-btn"
                    >
                      {uploadingPdf ? 'Parsing & Indexing Report...' : 'Process & Index Report'}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}
      </main>
      </div>

      {/* CORRECTIVE ACTION CREATION MODAL */}
      {actionModalOpen && actionReport && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: 6 }}>
              Assign Corrective Action
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Report {actionReport.report_uid} — Hazard: {actionReport.energy_source}
            </p>

            {/* Hierarchy of Controls Recommendations */}
            {recommendedControls.length > 0 && (
              <div style={{ background: 'rgba(0, 229, 255, 0.05)', border: '1px solid var(--border-glow)', padding: 14, borderRadius: 8, marginBottom: 16 }}>
                <strong style={{ color: 'var(--accent-cyan)', fontSize: '0.85rem' }}>💡 Recommended Controls (Hierarchy of Controls):</strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
                  {recommendedControls.map((rec, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 10,
                        background: 'rgba(0,0,0,0.3)',
                        borderRadius: 6,
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        border: '1px solid rgba(0, 229, 255, 0.12)'
                      }}
                      onClick={() => setActionForm({
                        ...actionForm,
                        title: rec.title,
                        description: rec.description,
                        hierarchy_level: rec.hierarchy_level
                      })}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, flexWrap: 'wrap', gap: 4 }}>
                        <div style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>[{rec.hierarchy_level}] {rec.title}</div>
                        {rec.target_barrier && (
                          <span className="badge" style={{ fontSize: '0.7rem', background: 'rgba(255,255,255,0.08)', color: 'var(--text-dim)' }}>
                            Target: {rec.target_barrier}
                          </span>
                        )}
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', lineHeight: 1.4 }}>{rec.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <form onSubmit={handleSaveAction} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Action Title</label>
                <input
                  type="text"
                  className="input-control"
                  value={actionForm.title}
                  onChange={(e) => setActionForm({ ...actionForm, title: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Hierarchy of Controls Level</label>
                <select
                  className="input-control"
                  value={actionForm.hierarchy_level}
                  onChange={(e) => setActionForm({ ...actionForm, hierarchy_level: e.target.value })}
                >
                  <option value="Elimination">Elimination (Most Effective)</option>
                  <option value="Substitution">Substitution</option>
                  <option value="Engineering Controls">Engineering Controls (Physical Barrier / Interlock)</option>
                  <option value="Administrative Controls">Administrative Controls (Procedures / JHA)</option>
                  <option value="PPE">PPE (Least Effective)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Action Scope & Implementation Details</label>
                <textarea
                  rows={3}
                  className="input-control"
                  value={actionForm.description}
                  onChange={(e) => setActionForm({ ...actionForm, description: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Action Owner / Lead</label>
                  <input
                    type="text"
                    className="input-control"
                    placeholder="e.g. Chief Maintenance Engineer"
                    value={actionForm.owner_name}
                    onChange={(e) => setActionForm({ ...actionForm, owner_name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target Completion Date</label>
                  <input
                    type="date"
                    className="input-control"
                    value={actionForm.target_date}
                    onChange={(e) => setActionForm({ ...actionForm, target_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 14 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setActionModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" id="save-action-submit-btn">
                  Create Action & Lock Verification Gate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* INDEPENDENT VERIFICATION GATE MODAL */}
      {verifyModalOpen && verifyingAction && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <ShieldAlert size={24} style={{ color: 'var(--accent-emerald)' }} />
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                Independent Verification Gate
              </h2>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 16 }}>
              Action {verifyingAction.action_uid}: <strong>{verifyingAction.title}</strong>
            </p>

            <div style={{ background: 'rgba(255, 153, 0, 0.1)', border: '1px solid rgba(255, 153, 0, 0.3)', padding: 12, borderRadius: 8, fontSize: '0.8rem', marginBottom: 16 }}>
              ⚠️ <strong>False Closure Prevention Rule:</strong> An action cannot be closed simply because a work order is signed. Independent physical inspection notes and authorized verifier sign-off are legally required.
            </div>

            <form onSubmit={handleVerifyAction} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Authorized Safety Verifier Name / ID</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Inspector David Vance (Cert #8821)"
                  value={verificationForm.verified_by}
                  onChange={(e) => setVerificationForm({ ...verificationForm, verified_by: e.target.value })}
                  required
                  id="verifier-name-input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Physical Verification Evidence Notes (min. 10 characters)</label>
                <textarea
                  rows={4}
                  className="input-control"
                  placeholder="Describe the physical check: Was the interlock tested? Was the static line proof-tested? Was the relief valve tag inspected?"
                  value={verificationForm.verification_notes}
                  onChange={(e) => setVerificationForm({ ...verificationForm, verification_notes: e.target.value })}
                  required
                  id="verification-notes-input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Inspection File / Photo Reference</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. WorkOrder_Signoff_Doc_4402.pdf"
                  value={verificationForm.verification_attachment}
                  onChange={(e) => setVerificationForm({ ...verificationForm, verification_attachment: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 14 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setVerifyModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-success" id="confirm-verification-submit-btn">
                  Sign Off & Confirm Verified Closure
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
