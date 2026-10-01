import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { documents, memory, orchestration } from '../api/client';

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
  pipelineTrace: { stage: string; status: string; detail: string }[];
  task?: string;
  llmProvider: string;
  correctionPerformed: boolean;
  claims: { claim: string; status: string; confidence: number; evidence_ids?: number[] }[];
  rerankingExplanation: string;
  timestamp: Date;
}

export const Chat = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([]);
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([]);
    const [searchParams] = useSearchParams();

    useEffect(() => {
      const recordId = searchParams.get('history');
      if (!recordId) return;
      memory.record(recordId).then((response) => {
        const record = response.data;
        const saved = record.response || {};
        setMessages([{
          id: record.id,
          query: record.query,
          answer: saved.answer || 'Saved analysis has no answer content.',
          intent: record.intent,
          retrievalStrategy: record.strategy,
          rerankerUsed: Boolean(saved.pipeline_trace?.some((step: any) => step.stage === 'cross_encoder_reranking' && step.detail === 'Applied')),
          sources: saved.sources || [],
          confidence: Number(record.confidence || 0),
          explanations: saved.explanations || [],
          verification: saved.verification,
          report: saved.report || '',
          pipelineTrace: saved.pipeline_trace || [],
          task: saved.task,
          llmProvider: saved.llm_provider || 'saved analysis',
          correctionPerformed: Boolean(saved.correction_performed),
          claims: saved.claims || [],
          rerankingExplanation: saved.reranking_explanation || '',
          timestamp: new Date(record.created_at),
        }]);
      }).catch((err: any) => setError(err.response?.data?.detail || 'Could not load saved analysis'));
    }, [searchParams]);

    useEffect(() => {
        const documentId = searchParams.get('document');
        documents.list(undefined, 1, 100).then((response) => {
          setAvailableDocuments(response.data);
          if (documentId && response.data.some((doc: any) => doc.id === documentId)) setSelectedDocumentIds([documentId]);
        }).catch(() => undefined);
      }, [searchParams]);
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await orchestration.query(query, 8, selectedDocumentIds);
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
        pipelineTrace: response.data.pipeline_trace || [],
        task: response.data.task,
        llmProvider: response.data.llm_provider || 'fallback:local',
        correctionPerformed: Boolean(response.data.correction_performed),
        claims: response.data.claims || [],
        rerankingExplanation: response.data.reranking_explanation || '',
        timestamp: new Date(),
      };

      setMessages((current) => [message, ...current]);
      setQuery('');
    } catch (err: any) {
      setError(err.response?.status === 428 ? 'AI analysis is locked. Open Settings and verify a provider or select the local fallback.' : err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="chat-layout">
      <section className="panel card chat-panel">
        <div className="section-title">
          <div>
            <span className="eyebrow">LANGGRAPH WORKSPACE</span>
            <h2>Ask your corpus</h2>
            <p className="muted chat-intro">Every answer runs through retrieval, an agent task, claim extraction, evidence verification, and explainability.</p>
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

        {availableDocuments.length > 0 && <div className="field evidence-picker"><span>Evidence scope</span><div className="doc-picker">{availableDocuments.map((doc) => <label className={`picker-item ${selectedDocumentIds.includes(doc.id) ? 'selected' : ''}`} key={doc.id}><input type="checkbox" checked={selectedDocumentIds.includes(doc.id)} onChange={() => setSelectedDocumentIds((current) => current.includes(doc.id) ? current.filter((id) => id !== doc.id) : [...current, doc.id])} /><span><strong>{doc.title}</strong><small>{doc.chunk_count || 0} indexed chunks</small></span></label>)}</div><small className="muted">Leave empty to search your full private library.</small></div>}

        {error && <div className="notice error">{error}</div>}

        {messages.length === 0 && !loading && (
          <div className="empty-state">
            <h3>No questions yet</h3>
            <p className="muted">Upload documents first, then ask a grounded question here.</p>
            <Link className="primary link-button" to="/upload">Upload evidence</Link>
          </div>
        )}

        {loading && (
          <div className="pipeline-live" aria-live="polite">
            <strong>TrustRAG is processing your query</strong>
            <span>Analyzing query, selecting retrieval, verifying evidence, and preparing explanation...</span>
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
                <span>Verification: {message.verification?.verification_status || 'unknown'}</span>
                <span>Agent: {message.task || 'qa'}</span>
              </div>
              <pre className="answer-text">{message.answer}</pre>

              <div className="result-grid">
                <div className="evidence-panel ai-panel">
                  <h3>AI execution</h3>
                  <p><strong>Provider:</strong> {message.llmProvider}</p>
                  <p><strong>Selected agent:</strong> {(message.task || 'qa').toUpperCase()}</p>
                  <p><strong>Correction search:</strong> {message.correctionPerformed ? 'performed' : 'not required'}</p>
                  <p><strong>Why this ranking:</strong> {message.rerankingExplanation}</p>
                  <div className="claim-list">
                    {message.claims.map((claim, index) => <div className={`claim claim-${claim.status.toLowerCase()}`} key={`${claim.claim}-${index}`}><strong>{claim.status}</strong><span>{claim.claim}</span><small>{(claim.confidence * 100).toFixed(0)}% claim confidence{claim.evidence_ids?.length ? ` · evidence ${claim.evidence_ids.map((id) => `[${id}]`).join(', ')}` : ''}</small></div>)}
                  </div>
                </div>
                <div className="evidence-panel">
                  <h3>Verification</h3>
                  <div className="confidence-bar">
                    <span style={{ width: `${Math.round(message.confidence * 100)}%` }} />
                  </div>
                  <p>
                    Confidence: {(message.confidence * 100).toFixed(1)}%
                    {message.verification?.hallucination_risk ? ` | Risk: ${message.verification.hallucination_risk}` : ''}
                    {message.verification?.evidence_score !== undefined ? ` | Evidence: ${(message.verification.evidence_score * 100).toFixed(1)}%` : ''}
                    {message.verification?.ets !== undefined ? ` | ETS: ${(message.verification.ets * 100).toFixed(1)}%` : ''}
                    {message.verification?.eif !== undefined ? ` | EIF: ${(message.verification.eif * 100).toFixed(1)}%` : ''}
                  </p>
                  {message.verification?.citation_completeness !== undefined && <p>Citation completeness: {(message.verification.citation_completeness * 100).toFixed(1)}%</p>}
                  {message.verification?.conflicts?.length > 0 && <div className="notice error">Conflicting evidence detected. Review the cited passages before relying on this answer.</div>}
                </div>
                <div className="evidence-panel">
                  <h3>Pipeline trace</h3>
                  <div className="trace-list">
                    {message.pipelineTrace.map((step) => (
                      <div className="trace-item" key={step.stage}>
                        <span className="trace-dot" />
                        <div><strong>{step.stage.replaceAll('_', ' ')}</strong><small>{step.detail}</small></div>
                      </div>
                    ))}
                  </div>
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
                    <strong>[{source.citation_id || index + 1}] {source.title}</strong>
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
