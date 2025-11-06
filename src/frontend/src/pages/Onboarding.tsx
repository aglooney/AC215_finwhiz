import { useState } from 'react';
import { TrendingUp, Shield } from 'lucide-react';
import type { UserProfile } from '../types';

interface OnboardingProps {
  onComplete: (profile: UserProfile) => void;
}

export default function Onboarding({ onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<Partial<UserProfile>>({
    riskTolerance: 'moderate',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (step === 1) {
      setStep(2);
    } else {
      onComplete(profile as UserProfile);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-800 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {step === 1 ? (
          <div className="card">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center gap-2 mb-4">
                <TrendingUp className="w-12 h-12 text-primary-600" />
                <h1 className="text-4xl font-bold text-gray-900">FinWhiz</h1>
              </div>
              <p className="text-xl text-gray-600">Your AI-Powered Financial Education Assistant</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="age" className="block text-sm font-semibold text-gray-700 mb-2">
                  What is your current age?
                </label>
                <input
                  type="number"
                  id="age"
                  min="18"
                  max="100"
                  required
                  className="input-field"
                  value={profile.age || ''}
                  onChange={(e) => setProfile({ ...profile, age: parseInt(e.target.value) })}
                  placeholder="e.g., 30"
                />
              </div>

              <div>
                <label htmlFor="retirementAge" className="block text-sm font-semibold text-gray-700 mb-2">
                  What age do you plan to retire?
                </label>
                <input
                  type="number"
                  id="retirementAge"
                  min={profile.age || 18}
                  max="100"
                  required
                  className="input-field"
                  value={profile.retirementAge || ''}
                  onChange={(e) => setProfile({ ...profile, retirementAge: parseInt(e.target.value) })}
                  placeholder="e.g., 65"
                />
              </div>

              <div>
                <label htmlFor="investmentGoal" className="block text-sm font-semibold text-gray-700 mb-2">
                  What is your primary investment goal?
                </label>
                <textarea
                  id="investmentGoal"
                  rows={3}
                  required
                  className="input-field"
                  value={profile.investmentGoal || ''}
                  onChange={(e) => setProfile({ ...profile, investmentGoal: e.target.value })}
                  placeholder="e.g., Save for retirement and achieve financial independence"
                />
              </div>

              <button type="submit" className="btn-primary w-full">
                Continue
              </button>
            </form>
          </div>
        ) : (
          <div className="card">
            <div className="text-center mb-8">
              <Shield className="w-12 h-12 text-primary-600 mx-auto mb-4" />
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Risk Assessment</h2>
              <p className="text-gray-600">Help us understand your investment comfort level</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-3">
                <label className="block">
                  <input
                    type="radio"
                    name="riskTolerance"
                    value="conservative"
                    checked={profile.riskTolerance === 'conservative'}
                    onChange={() => setProfile({ ...profile, riskTolerance: 'conservative' })}
                    className="mr-3"
                  />
                  <span className="font-semibold">Conservative</span>
                  <p className="ml-6 text-sm text-gray-600">
                    I prefer to minimize risk and protect my capital, even if it means lower returns.
                  </p>
                </label>

                <label className="block">
                  <input
                    type="radio"
                    name="riskTolerance"
                    value="moderate"
                    checked={profile.riskTolerance === 'moderate'}
                    onChange={() => setProfile({ ...profile, riskTolerance: 'moderate' })}
                    className="mr-3"
                  />
                  <span className="font-semibold">Moderate</span>
                  <p className="ml-6 text-sm text-gray-600">
                    I'm comfortable with some risk to achieve a balance between growth and stability.
                  </p>
                </label>

                <label className="block">
                  <input
                    type="radio"
                    name="riskTolerance"
                    value="aggressive"
                    checked={profile.riskTolerance === 'aggressive'}
                    onChange={() => setProfile({ ...profile, riskTolerance: 'aggressive' })}
                    className="mr-3"
                  />
                  <span className="font-semibold">Aggressive</span>
                  <p className="ml-6 text-sm text-gray-600">
                    I'm willing to accept higher risk for the potential of greater long-term returns.
                  </p>
                </label>
              </div>

              <div className="flex gap-4 pt-4">
                <button type="button" onClick={() => setStep(1)} className="btn-secondary flex-1">
                  Back
                </button>
                <button type="submit" className="btn-primary flex-1">
                  Get Started
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
