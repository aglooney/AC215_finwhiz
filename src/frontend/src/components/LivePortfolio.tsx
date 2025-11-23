import { useEffect, useState } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, DollarSign, PieChart } from 'lucide-react';
import { api } from '../services/api';

interface Holding {
  ticker: string;
  name: string;
  shares: number;
  original_value: number;
  current_price: number;
  current_value: number;
  gain_loss: number;
  gain_loss_percent: number;
  day_change: number;
  day_change_percent: number;
}

interface LivePortfolioData {
  total_current_value: number;
  total_original_value: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
  holdings: Holding[];
  account_name?: string;
  account_number?: string;
  account_type?: string;
  statement_date?: string;
  updated_at: string;
}

interface LivePortfolioProps {
  sessionId: string;
}

export default function LivePortfolio({ sessionId }: LivePortfolioProps) {
  const [portfolioData, setPortfolioData] = useState<LivePortfolioData | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPortfolioData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const [liveData, analyticsData] = await Promise.all([
        api.getPortfolioLive(sessionId),
        api.getPortfolioAnalytics(sessionId),
      ]);

      setPortfolioData(liveData);
      setAnalytics(analyticsData);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching portfolio data:', err);
      if (err.response?.status === 404) {
        setError('No portfolio found. Please upload a Fidelity portfolio statement.');
      } else {
        setError('Unable to load portfolio data. Please try again.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();
    // Auto-refresh every 5 minutes
    const interval = setInterval(() => fetchPortfolioData(true), 300000);
    return () => clearInterval(interval);
  }, [sessionId]);

  const handleRefresh = () => {
    fetchPortfolioData(true);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-red-200">
        <div className="flex items-center gap-2 text-red-600 mb-2">
          <DollarSign className="w-5 h-5" />
          <h3 className="font-bold">Portfolio Error</h3>
        </div>
        <p className="text-sm text-gray-600">{error}</p>
      </div>
    );
  }

  if (!portfolioData || !portfolioData.holdings || portfolioData.holdings.length === 0) {
    return (
      <div className="card">
        <h3 className="font-bold mb-2">Live Portfolio</h3>
        <p className="text-sm text-gray-600">
          No holdings found in your portfolio. Please upload a Fidelity portfolio statement with individual holdings.
        </p>
      </div>
    );
  }

  const isPositive = portfolioData.total_gain_loss >= 0;

  return (
    <div className="space-y-4">
      {/* Header with Refresh */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Live Portfolio</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Account Info */}
      {portfolioData.account_name && (
        <div className="card bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Account</p>
              <p className="font-semibold">{portfolioData.account_name}</p>
            </div>
            {portfolioData.account_number && (
              <div>
                <p className="text-gray-600">Account #</p>
                <p className="font-semibold">***{portfolioData.account_number.slice(-4)}</p>
              </div>
            )}
            {portfolioData.account_type && (
              <div>
                <p className="text-gray-600">Type</p>
                <p className="font-semibold">{portfolioData.account_type}</p>
              </div>
            )}
            {portfolioData.statement_date && (
              <div>
                <p className="text-gray-600">Statement Date</p>
                <p className="font-semibold">{portfolioData.statement_date}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-primary-50 border-primary-200">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-5 h-5 text-primary-600" />
            <h3 className="font-semibold text-gray-700">Current Value</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            ${portfolioData.total_current_value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Original: ${portfolioData.total_original_value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
        </div>

        <div className={`card ${isPositive ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-2 mb-2">
            {isPositive ? (
              <TrendingUp className="w-5 h-5 text-green-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600" />
            )}
            <h3 className="font-semibold text-gray-700">Total Gain/Loss</h3>
          </div>
          <p className={`text-3xl font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}${portfolioData.total_gain_loss.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </p>
          <p className={`text-lg font-semibold mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}{portfolioData.total_gain_loss_percent.toFixed(2)}%
          </p>
        </div>

        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <PieChart className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-700">Holdings</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{portfolioData.holdings.length}</p>
          {analytics && (
            <p className="text-xs text-gray-600 mt-1">
              Risk: {analytics.risk_metrics?.concentration_risk || 'Unknown'}
            </p>
          )}
        </div>
      </div>

      {/* Top/Bottom Performers */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {analytics.top_performers && analytics.top_performers.length > 0 && (
            <div className="card">
              <h3 className="font-bold text-green-600 mb-3 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Top Performers
              </h3>
              <div className="space-y-2">
                {analytics.top_performers.slice(0, 3).map((stock: any) => (
                  <div key={stock.ticker} className="flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-sm">{stock.ticker}</p>
                      <p className="text-xs text-gray-600">{stock.name}</p>
                    </div>
                    <p className="font-bold text-green-600 text-sm">
                      +{stock.gain_loss_percent.toFixed(2)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analytics.bottom_performers && analytics.bottom_performers.length > 0 && (
            <div className="card">
              <h3 className="font-bold text-red-600 mb-3 flex items-center gap-2">
                <TrendingDown className="w-5 h-5" />
                Needs Attention
              </h3>
              <div className="space-y-2">
                {analytics.bottom_performers.slice(0, 3).map((stock: any) => (
                  <div key={stock.ticker} className="flex justify-between items-center">
                    <div>
                      <p className="font-semibold text-sm">{stock.ticker}</p>
                      <p className="text-xs text-gray-600">{stock.name}</p>
                    </div>
                    <p className="font-bold text-red-600 text-sm">
                      {stock.gain_loss_percent.toFixed(2)}%
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Holdings Table */}
      <div className="card">
        <h3 className="font-bold mb-4">All Holdings</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left p-3 font-semibold">Symbol</th>
                <th className="text-left p-3 font-semibold">Name</th>
                <th className="text-right p-3 font-semibold">Shares</th>
                <th className="text-right p-3 font-semibold">Price</th>
                <th className="text-right p-3 font-semibold">Value</th>
                <th className="text-right p-3 font-semibold">Day Change</th>
                <th className="text-right p-3 font-semibold">Total Gain/Loss</th>
              </tr>
            </thead>
            <tbody>
              {portfolioData.holdings.map((holding) => {
                const isDayPositive = holding.day_change >= 0;
                const isTotalPositive = holding.gain_loss >= 0;

                return (
                  <tr key={holding.ticker} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="p-3 font-bold text-primary-600">{holding.ticker}</td>
                    <td className="p-3 text-gray-700">{holding.name}</td>
                    <td className="p-3 text-right">{holding.shares.toLocaleString()}</td>
                    <td className="p-3 text-right font-semibold">
                      ${holding.current_price.toFixed(2)}
                    </td>
                    <td className="p-3 text-right font-semibold">
                      ${holding.current_value.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}
                    </td>
                    <td className={`p-3 text-right font-semibold ${isDayPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {isDayPositive ? '+' : ''}{holding.day_change.toFixed(2)} ({holding.day_change_percent.toFixed(2)}%)
                    </td>
                    <td className={`p-3 text-right font-semibold ${isTotalPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {isTotalPositive ? '+' : ''}${holding.gain_loss.toFixed(2)}
                      <br />
                      <span className="text-xs">
                        ({isTotalPositive ? '+' : ''}{holding.gain_loss_percent.toFixed(2)}%)
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Last Updated */}
      <p className="text-xs text-gray-500 text-center">
        Last updated: {new Date(portfolioData.updated_at).toLocaleString()}
      </p>
    </div>
  );
}
