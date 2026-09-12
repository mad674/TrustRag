import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth endpoints
export const auth = {
  register: (username: string, email: string, password: string) =>
    apiClient.post('/api/users/register', { username, email, password }),
  login: (username: string, password: string) =>
    apiClient.post('/api/auth/token', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => apiClient.get('/api/users/me'),
};

// Document endpoints
export const documents = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  index: (docId: string) => apiClient.post(`/api/embeddings/index/${docId}`),
  list: (search?: string, page = 1, pageSize = 12) =>
    apiClient.get('/api/documents', {
      params: { ...(search ? { search } : {}), page, page_size: pageSize },
    }),
  get: (id: string) => apiClient.get(`/api/documents/${id}`),
  remove: (id: string) => apiClient.delete(`/api/documents/${id}`),
  summarize: (id: string, mode: 'short' | 'executive' | 'detailed' = 'executive') =>
    apiClient.post(`/api/documents/${id}/summarize`, null, { params: { mode } }),
  compare: (ids: string[], query: string) =>
    apiClient.post('/api/documents/compare', ids, { params: { query } }),
};

// Retrieval endpoints
export const retrieval = {
  vector: (query: string, topK: number = 10) =>
    apiClient.post('/api/retrieve/vector', { query, top_k: topK }),
  baseline: (query: string, topK: number = 10) =>
    apiClient.post('/api/retrieve/baseline', { query, top_k: topK }),
  adaptive: (query: string, topK: number = 10) =>
    apiClient.post('/api/adaptive/query', { query, top_k: topK }),
  adaptiveRag: (query: string, topK: number = 10) =>
    apiClient.post('/api/adaptive/rag', { query, top_k: topK }),
};

// Orchestration endpoint
export const orchestration = {
  query: (query: string, topK: number = 10) =>
    apiClient.post('/api/orchestrate/query', { query, top_k: topK }),
};

export const reports = {
  generate: (query: string, topK: number = 5, instructions?: string) =>
    apiClient.post('/api/reports/generate', { query, top_k: topK, instructions }, { responseType: 'blob' }),
};

export const llmSettings = {
  get: () => apiClient.get('/api/settings/llm'),
  validate: (payload: { provider: string; model: string; base_url?: string; api_key?: string; temperature: number; max_tokens: number }) =>
    apiClient.post('/api/settings/llm/validate', payload),
};

export const memory = {
  get: () => apiClient.get('/api/memory'),
  history: () => apiClient.get('/api/memory/history'),
};

export const evaluation = {
  compare: (query: string, topK: number = 10, relevantDocIds: string[] = []) =>
    apiClient.post('/api/evaluation/compare', {
      query,
      top_k: topK,
      relevant_doc_ids: relevantDocIds,
    }),
};

export default apiClient;
