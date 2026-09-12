import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { documents } from '../api/client';
import { memory } from '../api/client';

export const Dashboard = () => {
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [history, setHistory] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const pageSize = 12;

  useEffect(() => {
    loadDocuments(1);
    memory.history().then((response) => setHistory(response.data.slice(0, 4))).catch(() => undefined);
  }, []);

  const loadDocuments = async (requestedPage = page) => {
    setLoading(true);
    setError('');
    try {
      const response = await documents.list(search, requestedPage, pageSize);
      setDocs(response.data);
      setPage(requestedPage);
      setTotalDocuments(Number(response.headers['x-total-count'] || response.data.length));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const totalCharacters = docs.reduce((sum, doc) => sum + (doc.characters || 0), 0);
  const pageCount = Math.max(1, Math.ceil(totalDocuments / pageSize));

  return (
    <main className="workspace">
      <section className="dashboard-hero">
        <div>
          <span className="eyebrow">RESEARCH COMMAND CENTER</span>
          <h1>Turn scattered documents into confident answers.</h1>
          <p>Upload evidence, ask natural-language questions, and inspect exactly why TrustRAG reached each conclusion.</p>
          <div className="hero-actions">
            <Link className="primary link-button" to="/upload">Upload evidence <span>+</span></Link>
            <Link className="hero-text-link" to="/chat">Ask your first question <span>→</span></Link>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true"><span className="orbit-core">TR</span><span className="orbit-ring ring-one" /><span className="orbit-ring ring-two" /><b className="orbit-node node-one">BM25</b><b className="orbit-node node-two">DENSE</b><b className="orbit-node node-three">VERIFY</b></div>
      </section>
      <section className="metrics">
        <div className="panel metric">
          <span>Total documents</span>
          <strong>{totalDocuments}</strong>
        </div>
        <div className="panel metric">
          <span>Evidence indexed</span>
          <strong>{totalCharacters.toLocaleString()} chars</strong>
        </div>
        <div className="panel metric">
          <span>Research mode</span>
          <strong>Adaptive</strong>
        </div>
      </section>

      {history.length > 0 && <section className="panel card recent-panel"><div className="section-title"><div><span className="eyebrow">PRIVATE MEMORY</span><h2>Continue your research</h2></div><Link className="secondary link-button" to="/chat">Open chat</Link></div><div className="history-list">{history.map((item) => <Link className="history-item" to="/chat" key={item.id}><span>{item.query}</span><small>{item.strategy || 'adaptive'} · {item.verification_status || 'unverified'}</small></Link>)}</div></section>}

      <section className="panel card">
        <div className="section-title">
          <div>
            <span className="eyebrow">YOUR WORKSPACE</span>
            <h2>Your evidence library</h2>
            <p className="muted section-copy">Upload your papers and reports, then ask questions with transparent retrieval, citations, and verification.</p>
          </div>
          <Link className="primary link-button" to="/upload">Add evidence <span>+</span></Link>
        </div>
        <div className="library-toolbar"><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search your evidence library" /><button className="secondary" onClick={() => loadDocuments(1)}>Search</button></div>

        {error && <div className="notice error">{error}</div>}
        {loading && <p className="muted">Loading documents...</p>}

        {!loading && docs.length === 0 && (
          <div className="empty-state">
            <div className="empty-illustration"><span>⌁</span><span>✦</span><span>⌁</span></div>
            <span className="eyebrow">FIRST STEP</span><h3>Create your evidence library</h3>
            <p className="muted">Bring in a research paper, technical report, manual, or TXT file. TrustRAG will parse, chunk, embed, and index it for you.</p>
            <Link className="primary link-button" to="/upload">Upload your first document</Link>
          </div>
        )}

        <div className="doc-grid">
          {docs.map((doc) => (
            <article key={doc.id} className="doc-card">
              <div>
                <h3>{doc.title}</h3>
                <p className="muted">{doc.preview || 'No preview available'}</p>
              </div>
              <div className="doc-meta">
                <span>{doc.characters?.toLocaleString()} chars</span>
                <span>{doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'Unknown date'}</span>
              </div>
              <div className={`status status-${doc.processing_status || 'unknown'}`}>
                {doc.processing_status || 'unknown'} · {doc.chunk_count || 0} chunks
              </div>
              <Link className="secondary link-button" to={`/documents/${doc.id}`}>Open</Link>
            </article>
          ))}
        </div>
        {pageCount > 1 && (
          <div className="pagination" aria-label="Document pages">
            <button className="secondary" disabled={loading || page === 1} onClick={() => loadDocuments(page - 1)}>Previous</button>
            <span className="muted">Page {page} of {pageCount}</span>
            <button className="secondary" disabled={loading || page === pageCount} onClick={() => loadDocuments(page + 1)}>Next</button>
          </div>
        )}
      </section>
    </main>
  );
};

export default Dashboard;
