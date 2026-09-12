import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { llmSettings } from '../api/client';

const defaults = { provider: 'fallback', model: 'local-grounded', base_url: '', api_key: '', temperature: 0, max_tokens: 1200 };

export default function Settings() {
  const [form, setForm] = useState(defaults);
  const [hasKey, setHasKey] = useState(false);
  const [verified, setVerified] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  useEffect(() => { llmSettings.get().then((response) => { const data = response.data; setForm((current) => ({ ...current, provider: data.provider, model: data.model, base_url: data.base_url || '', temperature: data.temperature, max_tokens: data.max_tokens })); setHasKey(data.has_api_key); setVerified(data.is_verified); }).catch(() => setError('Could not load AI settings')); }, []);
  const update = (key: string, value: string | number) => setForm((current) => ({ ...current, [key]: value }));
  const selectProvider = (provider: string) => {
    const presets: Record<string, { model: string; base_url: string }> = {
      fallback: { model: 'local-grounded', base_url: '' },
      groq: { model: 'openai/gpt-oss-120b', base_url: 'https://api.groq.com/openai/v1' },
      openai: { model: 'gpt-4o-mini', base_url: 'https://api.openai.com/v1' },
      'openai-compatible': { model: 'your-model', base_url: '' },
    };
    setForm((current) => ({ ...current, provider, ...presets[provider] }));
    setVerified(false);
    setMessage('');
    setError('');
  };
  const save = async (event: React.FormEvent) => { event.preventDefault(); setBusy(true); setError(''); setMessage(''); try { const response = await llmSettings.validate({ ...form, api_key: form.api_key || undefined }); setHasKey(response.data.has_api_key); setVerified(response.data.is_verified); setForm((current) => ({ ...current, api_key: '' })); setMessage('Provider validated and encrypted for your account.'); } catch (err: any) { setVerified(false); setError(err.response?.data?.detail || 'Provider validation failed'); } finally { setBusy(false); } };
  return <main className="workspace"><section className="panel card settings-card"><span className="eyebrow">PRIVATE AI CONFIGURATION</span><h2>Choose your reasoning provider</h2><p className="muted">Your key is encrypted at rest and isolated to your account. Validation is required before an external LangGraph call can run.</p><form onSubmit={save} className="form-grid"><label className="field"><span>Provider</span><select value={form.provider} onChange={(event) => selectProvider(event.target.value)}><option value="fallback">Local grounded fallback</option><option value="groq">Groq</option><option value="openai">OpenAI</option><option value="openai-compatible">OpenAI-compatible endpoint</option></select></label><label className="field"><span>Model</span><input value={form.model} onChange={(event) => update('model', event.target.value)} placeholder="llama-3.3-70b-versatile" /></label><label className="field"><span>Base URL</span><input value={form.base_url} onChange={(event) => update('base_url', event.target.value)} placeholder="https://api.groq.com/openai/v1" /></label><label className="field"><span>API key {hasKey ? '(saved, encrypted)' : '(required for external providers)'}</span><input type="password" value={form.api_key} onChange={(event) => update('api_key', event.target.value)} placeholder={hasKey ? 'Enter a new key to rotate it' : 'Paste provider key'} autoComplete="off" /></label><div className="settings-controls"><label className="field"><span>Temperature: {form.temperature}</span><input type="range" min="0" max="2" step="0.1" value={form.temperature} onChange={(event) => update('temperature', Number(event.target.value))} /></label><label className="field"><span>Max tokens</span><input type="number" min="128" max="8000" value={form.max_tokens} onChange={(event) => update('max_tokens', Number(event.target.value))} /></label></div><button className="primary" disabled={busy}>{busy ? 'Validating provider...' : 'Validate and save provider'}</button></form>{verified && <div className="notice success"><strong>Provider ready.</strong> Your configuration is encrypted and LangGraph can now call this account’s model. <Link className="settings-chat-link" to="/chat">Open LangGraph Chat →</Link></div>}{message && <div className="notice success">{message}</div>}{error && <div className="notice error"><strong>Validation failed.</strong><br />{error}</div>}</section></main>;
}
