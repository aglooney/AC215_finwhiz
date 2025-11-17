import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { api } from '../services/api';

interface MarketIndex {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
}

export default function MarketOverview() {
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIndices = async () => {
      try {
        setLoading(true);
        const data = await api.getMarketIndices();
        setIndices(data.indices);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching market indices:', err);
        setError('Unable to load market data');
      } finally {
        setLoading(false);
      }
    };

    fetchIndices();
    // Refresh every 60 seconds
    const interval = setInterval(fetchIndices, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Market Overview</h3>
        <p className="text-gray-500 text-sm">Loading market data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <h3 className="text-lg font-bold mb-4">Market Overview</h3>
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-4">Market Overview</h3>
      <div className="grid grid-cols-2 gap-3">
        {indices.map((index) => (
          <div
            key={index.symbol}
            className="border border-gray-200 rounded-lg p-3 hover:border-primary-300 transition-colors"
          >
            <div className="text-xs text-gray-600 mb-1">{index.name}</div>
            <div className="font-bold text-gray-900 text-lg">
              {index.price.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </div>
            <div
              className={`flex items-center gap-1 text-sm font-semibold ${
                index.change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {index.change >= 0 ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span>
                {index.change >= 0 ? '+' : ''}
                {index.change.toFixed(2)} ({index.change_percent.toFixed(2)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}