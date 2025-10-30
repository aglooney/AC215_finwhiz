import axios from 'axios';
import type { Session, Message, QueryResponse, Document, UserProfile } from '../types';

const agentAPI = axios.create({
  baseURL: '/api/agent',
  headers: {
    'Content-Type': 'application/json',
  },
});

const llmAPI = axios.create({
  baseURL: '/api/llm',
  headers: {
    'Content-Type': 'application/json',
  },
});

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

  if (profile.riskTolerance === 'conservative') {
    stocks = Math.max(30, 100 - profile.age);
    bonds = Math.min(60, 80 - stocks);
    cash = 100 - stocks - bonds;
    description = 'A conservative portfolio focused on capital preservation with steady, reliable income.';
  } else if (profile.riskTolerance === 'moderate') {
    stocks = Math.max(40, 110 - profile.age);
    bonds = Math.min(50, 70 - stocks);
    cash = 100 - stocks - bonds;
    description = 'A balanced portfolio that seeks growth while managing risk through diversification.';
  } else {
    stocks = Math.max(60, 120 - profile.age);
    bonds = Math.min(35, 50 - stocks);
    cash = 100 - stocks - bonds;
    description = 'An aggressive portfolio focused on long-term growth with higher potential returns.';
  }

  return { stocks, bonds, cash, description };
}
