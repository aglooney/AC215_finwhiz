import { useState } from 'react';
import { Brain, Loader2, TrendingUp, TrendingDown, AlertTriangle, PieChart, Target } from 'lucide-react';

interface PortfolioAnalysisProps {
  sessionId: string;
}

export default function PortfolioAnalysis({ sessionId }: PortfolioAnalysisProps) {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [applyingTargets, setApplyingTargets] = useState(false);

  const handleAnalyze = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use relative URL to work with nginx proxy
      const response = await fetch(`/api/agent/sessions/${sessionId}/portfolio/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Analysis failed');
      }
      
      const data = await response.json();
      setAnalysis(data);
    } catch (err: any) {
      console.error('Error analyzing portfolio:', err);
      setError(err.message || 'Unable to analyze portfolio. Make sure you have uploaded a portfolio with holdings.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTargets = async () => {
    if (!analysis || !analysis.suggested_targets || Object.keys(analysis.suggested_targets).length === 0) {
      return;
    }

    try {
      setApplyingTargets(true);
      
      // Calculate specific targets
      const targetsResponse = await fetch(`/api/agent/sessions/${sessionId}/allocation/assets/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysis.suggested_targets)
      });
      
      if (!targetsResponse.ok) throw new Error('Failed to calculate targets');
      
      const targets = await targetsResponse.json();
      
      // Save targets
      const saveResponse = await fetch(`/api/agent/sessions/${sessionId}/allocation/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          targets: targets.targets,
          cash_target_percent: 0,
          ai_rationale: analysis.analysis.substring(0, 200) + '...'
        })
      });
      
      if (!saveResponse.ok) throw new Error('Failed to save targets');
      
      alert('✓ Asset allocation targets applied! Scroll down to see your target allocation plan.');
    } catch (error) {
      console.error('Error applying targets:', error);
      alert('✗ Failed to apply targets. Please try again.');
    } finally {
      setApplyingTargets(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-6 h-6 text-purple-600" />
          <h3 className="text-xl font-bold">AI Portfolio Analysis</h3>
        </div>
        
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Brain className="w-4 h-4" />
              Analyze My Portfolio
            </>
          )}
        </button>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Get AI-powered analysis of your actual holdings with specific recommendations for sector diversification, rebalancing, and risk management.
      </p>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {analysis && (
        <div className="space-y-4">
          {/* Portfolio Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
            <div>
              <p className="text-xs text-gray-600 mb-1">Total Value</p>
              <p className="text-lg font-bold text-gray-900">
                ${analysis.portfolio_summary.total_value.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Gain/Loss</p>
              <p className={`text-lg font-bold ${analysis.portfolio_summary.total_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analysis.portfolio_summary.total_gain_loss >= 0 ? '+' : ''}
                ${Math.abs(analysis.portfolio_summary.total_gain_loss).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2
                })}
              </p>
              <p className={`text-xs font-semibold ${analysis.portfolio_summary.total_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {analysis.portfolio_summary.total_gain_loss_percent >= 0 ? '+' : ''}
                {analysis.portfolio_summary.total_gain_loss_percent.toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Holdings</p>
              <p className="text-lg font-bold text-gray-900">{analysis.portfolio_summary.holdings_count}</p>
              <p className="text-xs text-gray-500">positions</p>
            </div>
            <div>
              <p className="text-xs text-gray-600 mb-1">Risk Level</p>
              <p className={`text-lg font-bold ${
                analysis.portfolio_summary.concentration_risk === 'High' ? 'text-red-600' :
                analysis.portfolio_summary.concentration_risk === 'Medium' ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {analysis.portfolio_summary.concentration_risk}
              </p>
              <p className="text-xs text-gray-500">
                Max: {analysis.portfolio_summary.largest_holding_percent.toFixed(1)}%
              </p>
            </div>
          </div>

          {/* Holdings Breakdown */}
          {analysis.holdings_breakdown && analysis.holdings_breakdown.length > 0 && (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-3">
                <PieChart className="w-5 h-5 text-gray-700" />
                <h4 className="font-semibold text-gray-900">Portfolio Composition</h4>
              </div>
              <div className="space-y-2">
                {analysis.holdings_breakdown
                  .sort((a: any, b: any) => b.percent_of_portfolio - a.percent_of_portfolio)
                  .map((holding: any) => (
                    <div key={holding.ticker} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-sm">{holding.ticker}</span>
                          <span className="text-xs text-gray-600 truncate">{holding.name}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{ width: `${holding.percent_of_portfolio}%` }}
                          />
                        </div>
                      </div>
                      <div className="ml-4 text-right">
                        <p className="text-sm font-bold text-gray-900">
                          {holding.percent_of_portfolio.toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-600">
                          ${holding.value.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                        </p>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Top/Bottom Performers */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysis.top_performers && analysis.top_performers.length > 0 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-green-900">Top Performers</h4>
                </div>
                <div className="space-y-2">
                  {analysis.top_performers.map((stock: any) => (
                    <div key={stock.ticker} className="flex justify-between items-center">
                      <div>
                        <p className="font-semibold text-sm text-gray-900">{stock.ticker}</p>
                        <p className="text-xs text-gray-600">{stock.name}</p>
                      </div>
                      <span className="text-green-600 font-bold text-sm">
                        +{stock.gain_loss_percent.toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {analysis.bottom_performers && analysis.bottom_performers.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingDown className="w-5 h-5 text-red-600" />
                  <h4 className="font-semibold text-red-900">Needs Attention</h4>
                </div>
                <div className="space-y-2">
                  {analysis.bottom_performers.map((stock: any) => (
                    <div key={stock.ticker} className="flex justify-between items-center">
                      <div>
                        <p className="font-semibold text-sm text-gray-900">{stock.ticker}</p>
                        <p className="text-xs text-gray-600">{stock.name}</p>
                      </div>
                      <span className="text-red-600 font-bold text-sm">
                        {stock.gain_loss_percent.toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* AI Analysis */}
          <div className="p-5 bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg">
            <div className="flex items-start gap-3 mb-4">
              <Brain className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h4 className="font-bold text-blue-900 text-lg">AI Recommendations</h4>
                <p className="text-xs text-blue-700 mt-1">Personalized analysis based on your holdings</p>
              </div>
              
              {/* Apply button if structured targets found */}
              {analysis.suggested_targets && Object.keys(analysis.suggested_targets).length > 0 && (
                <button
                  onClick={handleApplyTargets}
                  disabled={applyingTargets}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 transition-colors"
                >
                  {applyingTargets ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Applying...
                    </>
                  ) : (
                    <>
                      <Target className="w-4 h-4" />
                      Apply These Targets
                    </>
                  )}
                </button>
              )}
            </div>
            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <div className="prose prose-sm max-w-none">
                <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {analysis.analysis}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {!analysis && !loading && !error && (
        <div className="text-center py-8">
          <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-sm">
            Click "Analyze My Portfolio" to get AI-powered insights on your holdings
          </p>
        </div>
      )}
    </div>
  );
}