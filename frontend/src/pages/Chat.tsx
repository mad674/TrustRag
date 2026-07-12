import { useState } from 'react';
import { orchestration } from '../api/client';

interface Message {
  id: string;
  query: string;
  intent?: string;
  retrievalStrategy?: string;
  rerankerUsed?: boolean;
  answer: string;
  sources: any[];
  confidence: number;
  explanations: string[];
  verification?: Record<string, any>;
  report: string;
  timestamp: Date;
}

export const Chat = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await orchestration.query(query, 8);
      const message: Message = {
        id: Date.now().toString(),
        query,
        answer: response.data.answer,
        intent: response.data.intent,
        retrievalStrategy: response.data.retrieval_strategy,
        rerankerUsed: response.data.reranker_used,
        sources: response.data.sources || [],
        confidence: response.data.confidence || 0,
        explanations: response.data.explanations || [],
        verification: response.data.verification,
        report: response.data.report || '',
        timestamp: new Date(),
      };

      setMessages((current) => [message, ...current]);
      setQuery('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="chat-layout">
      <section className="panel card chat-panel">
        <div className="section-title">
          <div>
            <span className="badge">Multi-Agent RAG</span>
            <h2>Ask your corpus</h2>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="query-form">
          <textarea
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask for an answer, summary, comparison, citation, or research gap..."
            disabled={loading}
            rows={4}
          />
          <button className="primary" type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Reasoning...' : 'Run TrustRAG'}
          </button>
        </form>

        {error && <div className="notice error">{error}</div>}

        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <h3>No questions yet</h3>
            <p className="muted">Upload documents first, then ask a grounded question here.</p>
          </div>
        )}

        <div className="conversation">
          {messages.map((message) => (
            <article key={message.id} className="answer-block">
              <div className="question-row">
                <span>{message.timestamp.toLocaleTimeString()}</span>
                <strong>{message.query}</strong>
              </div>
              <div className="strategy-row">
                <span>Intent: {message.intent || 'unknown'}</span>
                <span>Strategy: {message.retrievalStrategy || 'unknown'}</span>
                <span>Reranker: {message.rerankerUsed ? 'on' : 'off'}</span>
              </div>
              <pre className="answer-text">{message.answer}</pre>

              <div className="result-grid">
                <div className="evidence-panel">
                  <h3>Verification</h3>
                  <div className="confidence-bar">
                    <span style={{ width: `${Math.round(message.confidence * 100)}%` }} />
                  </div>
                  <p>
                    Confidence: {(message.confidence * 100).toFixed(1)}%
                    {message.verification?.hallucination_risk ? ` | Risk: ${message.verification.hallucination_risk}` : ''}
                    {message.verification?.evidence_score !== undefined ? ` | Evidence: ${(message.verification.evidence_score * 100).toFixed(1)}%` : ''}
                  </p>
                </div>

                <div className="evidence-panel">
                  <h3>Explainability</h3>
                  <ul>
                    {message.explanations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="sources">
                <h3>Citations and Supporting Passages</h3>
                {message.sources.map((source, index) => (
                  <div className="source-row" key={`${source.doc_id}-${source.chunk_index}-${index}`}>
                    <strong>[{index + 1}] {source.title}</strong>
                    <span>
                      Score: {Number(source.relevance_score || 0).toFixed(3)}
                      {' | '}
                      Similarity: {Number(source.similarity_score || source.relevance_score || 0).toFixed(3)}
                      {' | '}
                      Strategy: {source.retrieval_strategy || message.retrievalStrategy}
                    </span>
                    <p>{source.text_preview}</p>
                  </div>
                ))}
              </div>

              {message.report && (
                <details className="report">
                  <summary>Generated report</summary>
                  <pre>{message.report}</pre>
                </details>
              )}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
};

export default Chat;
