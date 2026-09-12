import { useState } from 'react';
import { documents } from '../api/client';

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const stages = ['Validate file', 'Parse document', 'Clean and chunk text', 'Generate embeddings', 'Index evidence'];

  const submit = async () => {
    if (!file) return;
    setLoading(true);
    setUploading(true);
    setError('');
    setMessage('');
    try {
      const response = await documents.upload(file);
      setMessage(
        `Uploaded ${response.data.title} and indexed ${response.data.indexed_chunks} evidence chunks.`
      );
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setLoading(false);
      setUploading(false);
    }
  };

  return (
    <main className="content-grid">
      <section className="panel card">
        <span className="badge">Document Ingestion</span>
        <h2>Upload and index evidence</h2>
        <p className="muted">
          Supported formats: PDF, DOCX, TXT, and Markdown. Files are parsed, chunked, embedded, and added to the adaptive retriever immediately.
        </p>
        <div className="form-grid">
          <label className="field">
            <span>Select file</span>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.markdown"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="actions">
            <button className="primary" onClick={submit} disabled={!file || loading}>
              {loading ? 'Processing...' : 'Upload'}
            </button>
            {file && <span className="muted">{file.name}</span>}
          </div>
        </div>
        {message && <div className="notice success">{message}</div>}
        {error && <div className="notice error">{error}</div>}
      </section>

      <aside className="panel card">
        <h3>Pipeline</h3>
        <div className="list">
          {stages.map((step, index) => (
            <div className={`list-item pipeline-step ${uploading ? 'pipeline-step-active' : ''}`} style={{ animationDelay: `${index * 180}ms` }} key={step}><span className="step-index">{index + 1}</span><span>{step}</span><span className="step-state">{uploading ? 'processing' : message ? 'complete' : 'ready'}</span></div>
          ))}
        </div>
      </aside>
    </main>
  );
}
