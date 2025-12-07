import axios from 'axios';
import type {
  Document,
  QueryResponse,
  Session,
  SessionContext,
  UserProfile,
  UserProfileResponse,
  Message,
} from '../types';
import { mockApi } from './mockApi';

// Authentication types
export interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  expires_at: number;
}

export interface AuthResponse {
  user: AuthUser;
  session: AuthSession;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// Token management
const TOKEN_KEY = 'finwhiz_access_token';
const REFRESH_TOKEN_KEY = 'finwhiz_refresh_token';

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

export const removeTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

const USE_MOCK_API = import.meta.env.VITE_USE_MOCK_API === 'true';

// Get base URL from environment or default to relative paths
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

// Add request interceptor to include JWT token in Authorization header
const addAuthHeader = (config: any) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

agentAPI.interceptors.request.use(addAuthHeader);
llmAPI.interceptors.request.use(addAuthHeader);

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

const realApi = {
  // Authentication
  async signup(data: SignupRequest): Promise<AuthResponse> {
    const response = await agentAPI.post<AuthResponse>('/auth/signup', data);
    const { session } = response.data;
    if (session?.access_token) {
      setToken(session.access_token);
      setRefreshToken(session.refresh_token);
    }
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await agentAPI.post<AuthResponse>('/auth/signin', data);
    const { session } = response.data;
    if (session?.access_token) {
      setToken(session.access_token);
      setRefreshToken(session.refresh_token);
    }
    return response.data;
  },

  async logout(): Promise<void> {
    try {
      await agentAPI.post('/auth/signout');
    } finally {
      removeTokens();
    }
  },

  async getCurrentUser(): Promise<AuthUser> {
    const response = await agentAPI.get<AuthUser>('/auth/me');
    return response.data;
  },

  async refreshSession(): Promise<AuthSession> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await agentAPI.post<AuthSession>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    setToken(response.data.access_token);
    setRefreshToken(response.data.refresh_token);
    return response.data;
  },

  // Session Management
  async createSession(): Promise<Session> {
    const response = await agentAPI.post<Session>('/sessions/', {});
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

  async uploadPortfolio(sessionId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await agentAPI.post<Document>(`/sessions/${sessionId}/portfolio`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // LLM Query
  async query(query: string, sessionId?: string, topK: number = 5): Promise<QueryResponse> {
    const token = getToken();
    const response = await llmAPI.post<QueryResponse>('/query', {
      query,
      session_id: sessionId,
      top_k: topK,
      token: token,
    });
    return response.data;
  },

  // Get Session Context
  async getSessionContext(sessionId: string): Promise<SessionContext> {
    const response = await agentAPI.get<SessionContext>(`/sessions/${sessionId}/context`);
    return response.data;
  },


  async getPortfolioLive(sessionId: string): Promise<any> {
    const response = await agentAPI.get(`/sessions/${sessionId}/portfolio/live`);
    return response.data;
  },

  async getPortfolioAnalytics(sessionId: string): Promise<any> {
    const response = await agentAPI.get(`/sessions/${sessionId}/portfolio/analytics`);
    return response.data;
  },

  async getMarketQuote(ticker: string): Promise<any> {
    const response = await agentAPI.get(`/market/quote/${ticker}`);
    return response.data;
  },

  async getMarketIndices(): Promise<any> {
    const response = await agentAPI.get(`/market/indices`);
    return response.data;
  },

  async getStockHistory(ticker: string, period: string = '1mo'): Promise<any> {
    const response = await agentAPI.get(`/market/history/${ticker}`, {
      params: { period }
    });
    return response.data;
  },

  // User Profile
  async saveProfile(profile: UserProfile): Promise<UserProfileResponse> {
    const response = await agentAPI.put<UserProfileResponse>('/profile', {
      age: profile.age,
      retirement_age: profile.retirementAge,
      risk_tolerance: profile.riskTolerance,
      investment_goal: profile.investmentGoal,
    });
    return response.data;
  },

  async getProfile(): Promise<UserProfileResponse | null> {
    try {
      const response = await agentAPI.get<UserProfileResponse>('/profile');
      return response.data.profile_completed_at ? response.data : null;
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      return null;
    }
  },

};

export const api = USE_MOCK_API ? mockApi : realApi;

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
