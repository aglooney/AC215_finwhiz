export interface UserProfile {
  age: number;
  retirementAge: number;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  investmentGoal: string;
}

export interface Session {
  id: string;
  user_id: string;
  created_at?: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface Source {
  id: string;
  label: string;
  section?: string;
  url?: string;
  score?: number;
}

export interface QueryResponse {
  answer: string;
  context: string;
  sources: Source[];
}

export interface Document {
  id: string;
  session_id: string;
  document_type: 'w2' | '1099';
  gcs_uri: string;
  raw_metadata?: string;
  created_at: string;
}

export interface PortfolioRecommendation {
  stocks: number;
  bonds: number;
  cash: number;
  description: string;
}
