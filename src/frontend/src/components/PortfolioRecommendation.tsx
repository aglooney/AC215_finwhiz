import { PieChart, TrendingUp } from 'lucide-react';
import type { UserProfile } from '../types';
import { calculatePortfolio } from '../services/api';

interface PortfolioRecommendationProps {
  profile: UserProfile;
}

export default function PortfolioRecommendation({ profile }: PortfolioRecommendationProps) {
  const portfolio = calculatePortfolio(profile);
  const yearsToRetirement = profile.retirementAge - profile.age;

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <PieChart className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold">Your Personalized Portfolio</h3>
      </div>

      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Risk Level:</span>
          <span className="text-sm font-bold text-primary-600 uppercase">{profile.riskTolerance}</span>
        </div>
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Years to Retirement:</span>
          <span className="text-sm font-bold text-gray-900">{yearsToRetirement} years</span>
        </div>
      </div>

      <div className="space-y-4 mb-6">
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Stocks</span>
            <span className="text-sm font-bold text-gray-900">{portfolio.stocks}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-green-500 h-3 rounded-full transition-all"
              style={{ width: `${portfolio.stocks}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Bonds</span>
            <span className="text-sm font-bold text-gray-900">{portfolio.bonds}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-500 h-3 rounded-full transition-all"
              style={{ width: `${portfolio.bonds}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">Cash</span>
            <span className="text-sm font-bold text-gray-900">{portfolio.cash}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-yellow-500 h-3 rounded-full transition-all"
              style={{ width: `${portfolio.cash}%` }}
            />
          </div>
        </div>
      </div>

      <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
        <div className="flex gap-2 mb-2">
          <TrendingUp className="w-5 h-5 text-primary-600 flex-shrink-0" />
          <p className="text-sm text-gray-700">{portfolio.description}</p>
        </div>
      </div>
    </div>
  );
}
