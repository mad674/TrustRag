import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { documents } from '../api/client';

export default function DocumentDetail() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState<any>(null);
  const [summary, setSummary] = useState('');
  const [mode, setMode] = useState<'short' | 'executive' | 'detailed'>('executive');
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    documents.get(id).then((response) => setDocument(response.data)).catch((err) => setError(err.response?.data?.detail || 'Document unavailable')).finally(() => setLoading(false));
  }, [id]);

  const createSummary = async () => {
    setWorking(true);
    try { setSummary((await documents.summarize(id, mode)).data.summary); }
    catch (err: any) { setError(err.response?.data?.detail || 'Summary failed'); }
    finally { setWorking(false); }
  };

  const remove = async () => {
    if (!window.confirm('Delete this document and its indexed evidence?')) return;
    await documents.remove(id);
    navigate('/documents');
  };

  if (loading) return <main className="workspace"><div className="panel card"><p className="muted">Loading document...</p></div></main>;
  if (!document) return <main className="workspace"><div className="notice error">{error || 'Document not found'}</div></main>;

  return <main className="workspace">
    <section className="panel card detail-hero">
      <div><span className="badge">Document evidence</span><h2>{document.title}</h2><p className="muted">{document.filename} · {document.file_type?.toUpperCase()} · {document.chunk_count} chunks</p></div>
      <div className="actions"><Link className="secondary link-button" to="/documents">Back to library</Link><button className="secondary" onClick={remove}>Delete</button><Link className="primary link-button" to={`/chat?document=${id}`}>Ask about this</Link></div>
    </section>
    {error && <div className="notice error">{error}</div>}
    <section className="detail-grid">
      <article className="panel card"><h3>Metadata</h3><dl className="metadata"><dt>Status</dt><dd>{document.processing_status}</dd><dt>Characters</dt><dd>{document.content?.length?.toLocaleString()}</dd><dt>Uploaded</dt><dd>{document.created_at ? new Date(document.created_at).toLocaleString() : 'Unknown'}</dd></dl><h3>Extracted evidence</h3><pre className="document-text">{document.content}</pre></article>
      <aside className="panel card"><h3>Grounded summary</h3><div className="summary-controls"><select value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}><option value="short">Short</option><option value="executive">Executive</option><option value="detailed">Detailed</option></select><button className="primary" onClick={createSummary} disabled={working}>{working ? 'Generating...' : 'Generate'}</button></div>{summary ? <p className="answer-text">{summary}</p> : <p className="muted">Generate a summary from this document using the configured AI provider.</p>}</aside>
    </section>
  </main>;
}
