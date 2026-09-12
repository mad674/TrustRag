import { useState } from 'react';
import { reports } from '../api/client';

export default function Reports() {
  const [query, setQuery] = useState('Summarize the key evidence in my document collection.');
  const [instructions, setInstructions] = useState('Create an academic report with an executive summary, findings, citations, confidence, verification status, and limitations.');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const generate = async (event: React.FormEvent) => { event.preventDefault(); setLoading(true); setError(''); try { const response = await reports.generate(query, 8, instructions); const url = URL.createObjectURL(response.data); const link = document.createElement('a'); link.href = url; link.download = 'trustrag-report.pdf'; link.click(); URL.revokeObjectURL(url); } catch (err: any) { setError(err.response?.data?.detail || 'Report generation failed'); } finally { setLoading(false); } };
  return <main className="workspace"><section className="panel card report-builder"><span className="eyebrow">STRUCTURED RESEARCH OUTPUT</span><h2>Generate a grounded PDF report</h2><p className="muted">Your validated AI provider turns the query and cited evidence into a structured PDF. The report keeps confidence, verification, sources, and limitations visible.</p><form onSubmit={generate} className="form-grid"><label className="field"><span>Report question</span><textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={4} /></label><label className="field"><span>Report instructions</span><textarea value={instructions} onChange={(event) => setInstructions(event.target.value)} rows={4} /></label><button className="primary" disabled={loading || !query.trim()}>{loading ? 'Preparing PDF...' : 'Download PDF report'}</button></form>{error && <div className="notice error">{error}</div>}</section></main>;
}
