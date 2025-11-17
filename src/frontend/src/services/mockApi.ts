import type {
  Session,
  Message,
  QueryResponse,
  Document,
  UserProfile,
  SessionContext,
} from '../types';

// Mock delay to simulate API calls
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const mockDocumentsBySession = new Map<string, Document[]>();
const mockSessionUsers = new Map<string, string>();

const getSessionDocuments = (sessionId: string) => {
  if (!mockDocumentsBySession.has(sessionId)) {
    mockDocumentsBySession.set(sessionId, []);
  }
  return mockDocumentsBySession.get(sessionId)!;
};

// Mock LLM responses based on query keywords
const mockLLMResponses: Record<string, string> = {
  'default': "I'm FinWhiz, your financial education assistant. I can help you understand financial concepts, analyze documents, and provide guidance on investing, taxes, and retirement planning. Feel free to ask me anything!",
  'w-2': "A W-2 form, officially called the 'Wage and Tax Statement,' is an IRS tax form that reports your annual wages and the amount of taxes withheld from your paycheck. Your employer must send you a W-2 by January 31st each year for the previous tax year. It shows important information like federal income tax withheld, Social Security wages and taxes, Medicare wages and taxes, and state/local tax information.",
  'stocks': "When choosing stocks to invest in, consider several key factors: your risk tolerance, investment timeline, financial goals, and the need for diversification. For beginners, index funds and ETFs are often recommended as they provide instant diversification across many companies, reducing individual stock risk. Always research companies' fundamentals, consider their growth potential, and align investments with your overall financial strategy.",
  '1099': "Form 1099 is used to report various types of income other than wages, salaries, and tips (which are reported on W-2s). Common types include: 1099-INT for interest income from banks, 1099-DIV for dividends from investments, 1099-MISC for miscellaneous income like freelance work, and 1099-NEC for non-employee compensation. You'll receive these forms if you earned over certain threshold amounts in these categories.",
  'portfolio': "Your portfolio allocation should align with your age, risk tolerance, and investment goals. A common rule of thumb is to subtract your age from 110 or 120 to determine your stock allocation percentage, with the remainder in bonds and cash. However, this is just a starting point - your specific situation, risk tolerance, and goals should ultimately guide your decisions.",
  'retirement': "Retirement planning involves saving and investing to build wealth for your post-working years. Key retirement accounts include: 401(k)s (employer-sponsored with potential matching), Traditional IRAs (tax-deductible contributions), and Roth IRAs (tax-free withdrawals in retirement). Each has different contribution limits, tax advantages, and withdrawal rules. Starting early and contributing consistently are keys to successful retirement planning.",
  'tax': "Taxes are mandatory payments to federal, state, and local governments. Understanding tax brackets, deductions, and credits can help you minimize your tax burden legally. Common strategies include maximizing retirement contributions, claiming eligible deductions, and tax-loss harvesting in investment accounts.",
};

function getMockResponse(query: string): string {
  const lowerQuery = query.toLowerCase();
  if (lowerQuery.includes('w-2') || lowerQuery.includes('w2')) return mockLLMResponses['w-2'];
  if (lowerQuery.includes('stock') || lowerQuery.includes('invest')) return mockLLMResponses['stocks'];
  if (lowerQuery.includes('1099')) return mockLLMResponses['1099'];
  if (lowerQuery.includes('portfolio') || lowerQuery.includes('allocation')) return mockLLMResponses['portfolio'];
  if (lowerQuery.includes('retirement') || lowerQuery.includes('retire')) return mockLLMResponses['retirement'];
  if (lowerQuery.includes('tax')) return mockLLMResponses['tax'];
  return mockLLMResponses['default'];
}

export const mockApi = {
  // Session Management
  async createSession(userId: string): Promise<Session> {
    await delay(300);
    const sessionId = crypto.randomUUID();
    console.log('✓ Mock: Created session', sessionId);
    mockSessionUsers.set(sessionId, userId);
    return {
      id: sessionId,
      user_id: userId,
      created_at: new Date().toISOString(),
    };
  },

  async addMessage(sessionId: string, role: 'user' | 'assistant', content: string): Promise<Message> {
    await delay(100);
    console.log('✓ Mock: Added message', { sessionId, role, content });
    return {
      role,
      content,
      timestamp: new Date().toISOString(),
    };
  },

  // Document Upload
  async uploadW2(sessionId: string, file: File): Promise<Document> {
    await delay(1500); // Simulate processing time
    console.log('✓ Mock: Uploaded W-2', file.name);
    const document = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      document_type: 'w2',
      gcs_uri: `mock://bucket/w2/${file.name}`,
      created_at: new Date().toISOString(),
    };
    getSessionDocuments(sessionId).push(document);
    return document;
  },

  async upload1099(sessionId: string, file: File): Promise<Document> {
    await delay(1500); // Simulate processing time
    console.log('✓ Mock: Uploaded 1099', file.name);
    const document = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      document_type: '1099',
      gcs_uri: `mock://bucket/1099/${file.name}`,
      created_at: new Date().toISOString(),
    };
    getSessionDocuments(sessionId).push(document);
    return document;
  },

  async uploadPortfolio(sessionId: string, file: File): Promise<Document> {
    await delay(1500);
    console.log('✓ Mock: Uploaded portfolio', file.name);
    const document = {
      id: crypto.randomUUID(),
      session_id: sessionId,
      document_type: 'portfolio',
      gcs_uri: `mock://bucket/portfolio/${file.name}`,
      created_at: new Date().toISOString(),
    };
    getSessionDocuments(sessionId).push(document);
    return document;
  },

  // LLM Query
  async query(query: string, _sessionId?: string, _topK: number = 5): Promise<QueryResponse> {
    await delay(800); // Simulate LLM processing
    console.log('✓ Mock: Querying LLM with:', query);

    const answer = getMockResponse(query);

    return {
      answer,
      context: 'Mock context from FinWhiz knowledge base',
      sources: [
        {
          id: '1',
          label: 'IRS Tax Guide',
          section: 'Tax Forms',
          url: 'https://www.irs.gov/forms-pubs',
        },
        {
          id: '2',
          label: 'Investopedia',
          section: 'Financial Education',
          url: 'https://www.investopedia.com',
        },
        {
          id: '3',
          label: 'SEC Investor Education',
          section: 'Investing Basics',
          url: 'https://www.investor.gov',
        },
      ],
    };
  },

  // Get Session Context
  async getSessionContext(sessionId: string): Promise<SessionContext> {
    await delay(100);
    console.log('✓ Mock: Getting session context', sessionId);
    return {
      session_id: sessionId,
      user_id: mockSessionUsers.get(sessionId) || crypto.randomUUID(),
      recent_messages: [],
      w2_fields: {},
      form1099_fields: {},
      portfolio_fields: {},
      documents: [...getSessionDocuments(sessionId)],
    };
  },

  async getPortfolioLive(_sessionId: string): Promise<any> {
    return {
      total_current_value: 150000,
      total_original_value: 140000,
      total_gain_loss: 10000,
      total_gain_loss_percent: 7.14,
      holdings: [
        {
          ticker: 'AAPL',
          name: 'Apple Inc.',
          shares: 100,
          original_value: 15000,
          current_price: 175.50,
          current_value: 17550,
          gain_loss: 2550,
          gain_loss_percent: 17.0,
          day_change: 2.5,
          day_change_percent: 1.4
        }
      ],
      account_name: 'Mock Portfolio',
      updated_at: new Date().toISOString()
    };
  },

  async getPortfolioAnalytics(_sessionId: string): Promise<any> {
    return {
      top_performers: [
        { ticker: 'AAPL', name: 'Apple Inc.', gain_loss_percent: 17.0 }
      ],
      bottom_performers: [],
      risk_metrics: {
        number_of_holdings: 1,
        largest_holding_percent: 100,
        concentration_risk: 'High'
      }
    };
  },

  async getMarketQuote(ticker: string): Promise<any> {
    return {
      ticker,
      name: `Mock ${ticker}`,
      price: 100.00,
      change: 1.50,
      change_percent: 1.52,
      volume: 1000000,
      updated_at: new Date().toISOString()
    };
  },

  async getMarketIndices(): Promise<any> {
    return {
      indices: [
        { symbol: '^GSPC', name: 'S&P 500', price: 4500, change: 25, change_percent: 0.56 },
        { symbol: '^DJI', name: 'Dow Jones', price: 35000, change: 150, change_percent: 0.43 },
        { symbol: '^IXIC', name: 'NASDAQ', price: 14000, change: 80, change_percent: 0.57 },
        { symbol: '^RUT', name: 'Russell 2000', price: 1800, change: 10, change_percent: 0.56 }
      ],
      updated_at: new Date().toISOString()
    };
  },

  async getStockHistory(ticker: string, period: string = '1mo'): Promise<any> {
    return {
      ticker,
      period,
      history: [
        { date: '2024-11-01', open: 100, high: 105, low: 99, close: 103, volume: 1000000 },
        { date: '2024-11-02', open: 103, high: 106, low: 102, close: 105, volume: 1100000 }
      ]
    };
  },

  async saveCustomAllocation(_sessionId: string, allocation: { stocks: number; bonds: number; cash: number }): Promise<any> {
    return { status: 'success', allocation };
  },

  async getCustomAllocation(_sessionId: string): Promise<any> {
    throw new Error('No custom allocation found'); // Mock returns 404
  },

  async saveAssetAllocationTarget(_sessionId: string, allocation: any): Promise<any> {
    return { status: 'success', allocation };
  },

  async getAssetAllocationTarget(_sessionId: string): Promise<any> {
    throw new Error('No asset allocation target found');
  },

  async calculateAssetTargets(_sessionId: string, targetPercentages: Record<string, number>): Promise<any> {
    return {
      targets: Object.entries(targetPercentages).map(([ticker, target_percent]) => ({
        ticker,
        target_percent,
        current_percent: 0,
        action: 'buy',
        shares_to_trade: 10,
        dollar_amount: 1000
      })),
      total_portfolio_value: 100000
    };
  },
};

// Portfolio calculation helper
export function calculatePortfolio(profile: UserProfile) {
  let stocks = 0;
  let bonds = 0;
  let cash = 0;
  let description = '';

  // Calculate based on age and risk tolerance
  if (profile.riskTolerance === 'conservative') {
    stocks = Math.max(20, Math.min(50, 100 - profile.age));
    bonds = Math.max(30, Math.min(60, 100 - stocks - 10));
    cash = 100 - stocks - bonds;
    description = 'A conservative portfolio focused on capital preservation with steady, reliable income.';
  } else if (profile.riskTolerance === 'moderate') {
    stocks = Math.max(40, Math.min(70, 110 - profile.age));
    bonds = Math.max(20, Math.min(50, 100 - stocks - 10));
    cash = 100 - stocks - bonds;
    description = 'A balanced portfolio that seeks growth while managing risk through diversification.';
  } else {
    stocks = Math.max(60, Math.min(90, 120 - profile.age));
    bonds = Math.max(5, Math.min(30, 100 - stocks - 5));
    cash = 100 - stocks - bonds;
    description = 'An aggressive portfolio focused on long-term growth with higher potential returns.';
  }

  // Ensure no negative values and totals to 100%
  stocks = Math.max(0, Math.min(100, Math.round(stocks)));
  bonds = Math.max(0, Math.min(100 - stocks, Math.round(bonds)));
  cash = 100 - stocks - bonds;

  return { stocks, bonds, cash, description };
}
