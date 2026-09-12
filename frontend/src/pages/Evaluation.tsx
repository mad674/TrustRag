import { useEffect, useState } from 'react';
import { documents, evaluation } from '../api/client';

type ComparisonRow = {
  mode: string;
  intent?: string;
  strategy?: string;
  reranker_used: boolean;
  confidence: number;
  evidence_score: number;
  hallucination_risk: string;
  precision_at_k: number;
  recall_at_k: number;
  latency_ms: number;
  source_count: number;
};

export default function Evaluation() {
  const [query, setQuery] = useState('What are the main findings in the corpus?');
  const [topK, setTopK] = useState(5);
  const [rows, setRows] = useState<ComparisonRow[]>([]);
  const [claim, setClaim] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [docs, setDocs] = useState<any[]>([]);
  const [relevantIds, setRelevantIds] = useState<string[]>([]);
  useEffect(() => { documents.list().then((response) => setDocs(response.data)).catch(() => undefined); }, []);

  const runComparison = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const response = await evaluation.compare(query, topK, relevantIds);
      setRows(response.data.results || []);
      setClaim(response.data.research_claim || '');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="workspace">
      <section className="panel card">
        <span className="badge">Research Evaluation</span>
        <h2>Compare retrieval strategies</h2>
        <p className="muted">Run the same query through dense baseline, fixed hybrid, reranked hybrid, and adaptive retrieval.</p>
        <form onSubmit={runComparison} className="form-grid">
          <label className="field">
            <span>Evaluation query</span>
            <textarea value={query} onChange={(event) => setQuery(event.target.value)} rows={3} />
          </label>
          <div className="evaluation-controls">
            <label className="field">
              <span>Top K</span>
              <input type="number" min={1} max={20} value={topK} onChange={(event) => setTopK(Number(event.target.value))} />
            </label>
            <div className="field"><span>Relevant evidence documents</span><div className="doc-picker evaluation-picker">{docs.map((doc) => <label className={`picker-item ${relevantIds.includes(doc.id) ? 'selected' : ''}`} key={doc.id}><input type="checkbox" checked={relevantIds.includes(doc.id)} onChange={() => setRelevantIds((current) => current.includes(doc.id) ? current.filter((id) => id !== doc.id) : [...current, doc.id])} /><span><strong>{doc.title}</strong><small>{doc.processing_status} · {doc.chunk_count} chunks</small></span></label>)}</div><small className="muted">Select the documents that contain the expected evidence. No UUIDs required.</small></div>
          </div>
          <button className="primary" type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Running experiment...' : 'Run comparison'}
          </button>
        </form>
        {error && <div className="notice error">{error}</div>}
      </section>

      {claim && <div className="notice success">{claim}</div>}

      {rows.length > 0 && (
        <section className="panel card">
          <div className="section-title">
            <div>
              <span className="badge">Experiment Results</span>
              <h2>Strategy comparison</h2>
            </div>
          </div>
          <div className="table-wrap">
            <table className="results-table">
              <thead>
                <tr>
                  <th>Mode</th><th>Strategy</th><th>Confidence</th><th>Evidence</th><th>Risk</th><th>P@K</th><th>R@K</th><th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.mode}>
                    <td><strong>{row.mode}</strong><small>{row.intent || 'unknown'}</small></td>
                    <td>{row.strategy || 'unknown'}{row.reranker_used ? ' + rerank' : ''}</td>
                    <td>{(row.confidence * 100).toFixed(1)}%</td>
                    <td>{(row.evidence_score * 100).toFixed(1)}%</td>
                    <td>{row.hallucination_risk}</td>
                    <td>{row.precision_at_k.toFixed(3)}</td>
                    <td>{row.recall_at_k.toFixed(3)}</td>
                    <td>{row.latency_ms.toFixed(1)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}
