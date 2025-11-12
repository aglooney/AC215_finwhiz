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

export type DocumentType = 'w2' | '1099' | 'portfolio';

export interface Document {
  id: string;
  session_id: string;
  document_type: DocumentType | string;
  gcs_uri: string;
  raw_metadata?: string;
  created_at: string;
}

export interface W2Fields {
  employee_name?: string | null;
  employee_ssn?: string | null;
  employer_name?: string | null;
  employer_ein?: string | null;
  wages_tips_other_comp?: string | null;
  federal_income_tax_withheld?: string | null;
  social_security_wages?: string | null;
  social_security_tax_withheld?: string | null;
  medicare_wages?: string | null;
  medicare_tax_withheld?: string | null;
  box12_codes?: string | null;
  state?: string | null;
  state_wages?: string | null;
  state_income_tax?: string | null;
}

export interface Form1099Fields {
  box1_interest_income?: number | string | null;
  box2_early_withdrawal_penalty?: number | string | null;
  box3_us_savings_bond_interest?: number | string | null;
  box4_federal_income_tax_withheld?: number | string | null;
  box5_investment_expenses?: number | string | null;
  box6_foreign_tax_paid?: number | string | null;
  box7_foreign_country?: number | string | null;
  box8_tax_exempt_interest?: number | string | null;
  box9_private_activity_bond_interest?: number | string | null;
  box10_market_discount?: number | string | null;
  box11_bond_premium?: number | string | null;
  box12_treasury_bond_premium?: number | string | null;
  box13_tax_exempt_bond_premium?: number | string | null;
  box14_cusip_number?: number | string | null;
  state?: number | string | null;
  state_id?: number | string | null;
  state_tax_withheld?: number | string | null;
}

export interface HoldingDetail {
  ticker?: string | null;
  name?: string | null;
  shares?: number | string | null;
  value?: number | string | null;
  asset_class?: string | null;
}

export interface PortfolioFields {
  total_portfolio_value?: number | string | null;
  account_name?: string | null;
  account_number?: string | null;
  account_type?: string | null;
  statement_date?: string | null;
  account_owner?: string | null;
  stocks_percentage?: number | string | null;
  bonds_percentage?: number | string | null;
  cash_percentage?: number | string | null;
  other_percentage?: number | string | null;
  holdings?: HoldingDetail[] | null;
  notes?: string | null;
}

export interface SessionContext {
  session_id: string;
  user_id: string;
  recent_messages: Message[];
  w2_fields?: W2Fields | null;
  form1099_fields?: Form1099Fields | null;
  portfolio_fields?: PortfolioFields | null;
  documents?: Document[] | null;
  summary?: string | null;
}

export interface PortfolioRecommendation {
  stocks: number;
  bonds: number;
  cash: number;
  description: string;
}
