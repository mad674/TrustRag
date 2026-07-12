import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { documents } from '../api/client';

export const Dashboard = () => {
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await documents.list();
      setDocs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const totalCharacters = docs.reduce((sum, doc) => sum + (doc.characters || 0), 0);

  return (
    <main className="workspace">
      <section className="metrics">
        <div className="panel metric">
          <span>Documents</span>
          <strong>{docs.length}</strong>
        </div>
        <div className="panel metric">
          <span>Indexed Text</span>
          <strong>{totalCharacters.toLocaleString()} chars</strong>
        </div>
        <div className="panel metric">
          <span>Retrieval</span>
          <strong>Hybrid</strong>
        </div>
      </section>

      <section className="panel card">
        <div className="section-title">
          <div>
            <span className="badge">Document Library</span>
            <h2>Evidence corpus</h2>
          </div>
          <Link className="primary link-button" to="/upload">Upload</Link>
        </div>

        {error && <div className="notice error">{error}</div>}
        {loading && <p className="muted">Loading documents...</p>}

        {!loading && docs.length === 0 && (
          <div className="empty-state">
            <h3>No documents yet</h3>
            <p className="muted">Upload a paper, report, policy, or manual to start querying with citations.</p>
            <Link className="primary link-button" to="/upload">Upload first document</Link>
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
              <Link className="secondary link-button" to="/chat">Query</Link>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
};

export default Dashboard;
