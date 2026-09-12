import { useEffect, useState } from 'react';
import { documents } from '../api/client';

export default function Compare() {
  const [docs, setDocs] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState('Compare the key findings and differences.');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { documents.list().then((response) => setDocs(response.data)).catch(() => setError('Could not load documents')); }, []);
  const toggle = (id: string) => setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  const compare = async (event: React.FormEvent) => { event.preventDefault(); if (selected.length < 2) return; setLoading(true); setError(''); try { setResult((await documents.compare(selected, query)).data); } catch (err: any) { setError(err.response?.data?.detail || 'Comparison failed'); } finally { setLoading(false); } };
  return <main className="workspace"><section className="panel card"><span className="badge">Evidence comparison</span><h2>Compare documents</h2><p className="muted">Select two or more indexed documents. The comparison is grounded in their extracted text.</p><form onSubmit={compare} className="form-grid"><label className="field"><span>Comparison question</span><textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={3} /></label><div className="doc-picker">{docs.map((doc) => <label className={`picker-item ${selected.includes(doc.id) ? 'selected' : ''}`} key={doc.id}><input type="checkbox" checked={selected.includes(doc.id)} onChange={() => toggle(doc.id)} /><span><strong>{doc.title}</strong><small>{doc.processing_status} · {doc.chunk_count} chunks</small></span></label>)}</div><button className="primary" disabled={loading || selected.length < 2}>{loading ? 'Comparing...' : `Compare ${selected.length} documents`}</button></form>{error && <div className="notice error">{error}</div>}</section>{result && <section className="panel card"><div className="section-title"><div><span className="badge">Grounded result</span><h2>{result.documents.map((doc: any) => doc.title).join(' vs ')}</h2></div><span className="status status-indexed">{result.provider}</span></div><pre className="answer-text">{result.answer}</pre><div className="notice">{result.verification}</div></section>}</main>;
}
