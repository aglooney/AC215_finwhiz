import { useState, useEffect } from 'react';
import { Target, TrendingUp, TrendingDown, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface TargetAllocationProps {
  sessionId: string;
}

interface AssetTarget {
  ticker: string;
  target_percent: number;
  current_percent: number;
  action: string;
  shares_to_trade: number;
  dollar_amount: number;
}

export default function TargetAllocation({ sessionId }: TargetAllocationProps) {
  const [targets, setTargets] = useState<AssetTarget[]>([]);
  const [cashTarget, setCashTarget] = useState<number>(0);
  const [rationale, setRationale] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [_error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTargets = async () => {
      try {
        setLoading(true);
        const response = await api.getAssetAllocationTarget(sessionId);
        if (response.allocation) {
          setTargets(response.allocation.targets || []);
          setCashTarget(response.allocation.cash_target_percent || 0);
          setRationale(response.allocation.ai_rationale || '');
        }
        setError(null);
      } catch (err) {
        // No targets set yet - this is fine
        setError(null);
      } finally {
        setLoading(false);
      }
    };

    loadTargets();
    
    // Refresh periodically
    const interval = setInterval(loadTargets, 10000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading) {
    return null; // Don't show anything while loading
  }

  if (targets.length === 0) {
    return null; // Don't show if no targets
  }

  return (
    <div className="card border-2 border-blue-300 bg-blue-50">
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-6 h-6 text-blue-600" />
        <h3 className="text-xl font-bold text-blue-900">Target Allocation Plan</h3>
      </div>

      {rationale && (
        <div className="mb-4 p-3 bg-white rounded-lg border border-blue-200">
          <p className="text-sm text-gray-700">{rationale}</p>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-blue-100 border-b-2 border-blue-300">
            <tr>
              <th className="text-left p-3 font-semibold text-blue-900">Asset</th>
              <th className="text-right p-3 font-semibold text-blue-900">Current</th>
              <th className="text-right p-3 font-semibold text-blue-900">Target</th>
              <th className="text-right p-3 font-semibold text-blue-900">Action</th>
              <th className="text-right p-3 font-semibold text-blue-900">Shares</th>
              <th className="text-right p-3 font-semibold text-blue-900">Amount</th>
            </tr>
          </thead>
          <tbody className="bg-white">
            {targets.map((target) => (
              <tr key={target.ticker} className="border-b border-blue-200 hover:bg-blue-50">
                <td className="p-3 font-bold text-primary-600">{target.ticker}</td>
                <td className="p-3 text-right font-semibold">{target.current_percent.toFixed(1)}%</td>
                <td className="p-3 text-right font-bold text-blue-700">{target.target_percent.toFixed(1)}%</td>
                <td className="p-3 text-right">
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${
                    target.action === 'buy' ? 'bg-green-100 text-green-700' :
                    target.action === 'sell' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {target.action === 'buy' && <TrendingUp className="w-3 h-3" />}
                    {target.action === 'sell' && <TrendingDown className="w-3 h-3" />}
                    {target.action === 'hold' && <CheckCircle className="w-3 h-3" />}
                    {target.action.toUpperCase()}
                  </span>
                </td>
                <td className={`p-3 text-right font-semibold ${
                  target.shares_to_trade > 0 ? 'text-green-600' :
                  target.shares_to_trade < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {target.shares_to_trade > 0 ? '+' : ''}{target.shares_to_trade.toFixed(0)}
                </td>
                <td className={`p-3 text-right font-semibold ${
                  target.dollar_amount > 0 ? 'text-green-600' :
                  target.dollar_amount < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {target.dollar_amount >= 0 ? '+' : ''}${target.dollar_amount.toLocaleString('en-US', {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0
                  })}
                </td>
              </tr>
            ))}
            
            {cashTarget > 0 && (
              <tr className="border-b border-blue-200 bg-yellow-50">
                <td className="p-3 font-bold text-yellow-700">Cash</td>
                <td className="p-3 text-right font-semibold">-</td>
                <td className="p-3 text-right font-bold text-blue-700">{cashTarget.toFixed(1)}%</td>
                <td className="p-3 text-right">
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-700">
                    RESERVE
                  </span>
                </td>
                <td className="p-3 text-right">-</td>
                <td className="p-3 text-right">-</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 p-3 bg-blue-100 border border-blue-300 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-700 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-blue-800">
            This is your AI-recommended target allocation. Execute trades gradually to reach these targets while monitoring market conditions.
          </p>
        </div>
      </div>
    </div>
  );
}