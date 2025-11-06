import type { Session, Message, QueryResponse, Document, UserProfile } from '../types';
import { mockApi } from './mockApi';

// Use mock API for all operations
// This provides a non-functional UI demo without requiring backend services
export const api = mockApi;

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
