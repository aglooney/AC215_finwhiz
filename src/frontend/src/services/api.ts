import axios from 'axios';
import type { Session, Message, QueryResponse, Document, UserProfile } from '../types';

// Get base URL from environment or default to relative paths
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

console.log('BASE_URL:', BASE_URL);

const agentAPI = axios.create({
  baseURL: `${BASE_URL}/api/agent`,
  headers: {
    'Content-Type': 'application/json',
  },
});

const llmAPI = axios.create({
  baseURL: `${BASE_URL}/api/llm`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout
});

// Add response interceptor for better error handling
const handleApiError = (error: any) => {
  if (error.response) {
    console.error('API Error Response:', error.response.data);
    console.error('Status:', error.response.status);
  } else if (error.request) {
    console.error('API No Response:', error.request);
  } else {
    console.error('API Error:', error.message);
  }
  return Promise.reject(error);
};

agentAPI.interceptors.response.use(
  (response) => response,
  handleApiError
);

llmAPI.interceptors.response.use(
  (response) => response,
  handleApiError
);

export const api = {
  // Session Management
  async createSession(userId: string): Promise<Session> {
    const response = await agentAPI.post<Session>('/sessions/', { user_id: userId });
    return response.data;
  },

  async addMessage(sessionId: string, role: 'user' | 'assistant', content: string): Promise<Message> {
    const response = await agentAPI.post<Message>(`/sessions/${sessionId}/messages`, {
      role,
      content,
    });
    return response.data;
  },

  // Document Upload
  async uploadW2(sessionId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await agentAPI.post<Document>(`/sessions/${sessionId}/w2`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async upload1099(sessionId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await agentAPI.post<Document>(`/sessions/${sessionId}/1099`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // LLM Query
  async query(query: string, sessionId?: string, topK: number = 5): Promise<QueryResponse> {
    const response = await llmAPI.post<QueryResponse>('/query', {
      query,
      session_id: sessionId,
      top_k: topK,
    });
    return response.data;
  },

  // Get Session Context
  async getSessionContext(sessionId: string): Promise<any> {
    const response = await agentAPI.get(`/sessions/${sessionId}/context`);
    return response.data;
  },
};

// Portfolio calculation helper
export function calculatePortfolio(profile: UserProfile) {
  let stocks = 0;
  let bonds = 0;
  let cash = 0;
  let description = '';

  // Calculate based on age and risk tolerance
  // Conservative: Lower stock allocation
  // Moderate: Balanced approach
  // Aggressive: Higher stock allocation

  if (profile.riskTolerance === 'conservative') {
    // Conservative: 30-50% stocks depending on age
    stocks = Math.max(20, Math.min(50, 100 - profile.age));
    bonds = Math.max(30, Math.min(60, 100 - stocks - 10));
    cash = 100 - stocks - bonds;
    description = 'A conservative portfolio focused on capital preservation with steady, reliable income.';
  } else if (profile.riskTolerance === 'moderate') {
    // Moderate: 40-70% stocks depending on age
    stocks = Math.max(40, Math.min(70, 110 - profile.age));
    bonds = Math.max(20, Math.min(50, 100 - stocks - 10));
    cash = 100 - stocks - bonds;
    description = 'A balanced portfolio that seeks growth while managing risk through diversification.';
  } else {
    // Aggressive: 60-90% stocks depending on age
    stocks = Math.max(60, Math.min(90, 120 - profile.age));
    bonds = Math.max(5, Math.min(30, 100 - stocks - 5));
    cash = 100 - stocks - bonds;
    description = 'An aggressive portfolio focused on long-term growth with higher potential returns.';
  }

  // Ensure no negative values and totals to 100%
  stocks = Math.max(0, Math.min(100, stocks));
  bonds = Math.max(0, Math.min(100 - stocks, bonds));
  cash = 100 - stocks - bonds;

  return { stocks, bonds, cash, description };
}
