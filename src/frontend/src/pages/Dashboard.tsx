import { useState } from 'react';
import { LogOut, User, MessageSquare, Upload, PieChart as PieChartIcon } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import DocumentUpload from '../components/DocumentUpload';
import PortfolioRecommendation from '../components/PortfolioRecommendation';
import LivePortfolio from '../components/LivePortfolio';
import MarketOverview from '../components/MarketOverview';
import type { UserProfile, Document } from '../types';

interface DashboardProps {
  profile: UserProfile;
  sessionId: string;
  onLogout: () => void;
}

type Tab = 'chat' | 'upload' | 'portfolio';

export default function Dashboard({ profile, sessionId, onLogout }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [uploadedDocuments, setUploadedDocuments] = useState<Document[]>([]);

  const handleDocumentsChange = (documents: Document[]) => {
    setUploadedDocuments(documents);
  };

  return (
    <div className="min-h-screen bg-cream-100">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="bg-cream-100 rounded-lg p-2 border border-cream-300">
              <img
                src="/logo-icon.png"
                alt="FinWhiz"
                className="h-12 object-contain"
              />
            </div>



            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-cream-100 rounded-lg border border-cream-300">
                <User className="w-5 h-5 text-primary-600" />
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">Age {profile.age}</p>
                  <p className="text-xs text-gray-600">Retires at {profile.retirementAge}</p>
                </div>
              </div>
              <button
                onClick={onLogout}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-cream-200 rounded-lg transition-colors"
              >
                <LogOut className="w-5 h-5" />
                <span className="text-sm font-medium">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>


      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            {/* Navigation Tabs */}
            <div className="card">
              <nav className="space-y-2">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === 'chat'
                      ? 'bg-primary-700 text-white'
                      : 'text-gray-700 hover:bg-cream-100'
                  }`}
                >
                  <MessageSquare className="w-5 h-5" />
                  <span className="font-medium">Chat</span>
                </button>

                <button
                  onClick={() => setActiveTab('upload')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === 'upload'
                      ? 'bg-primary-700 text-white'
                      : 'text-gray-700 hover:bg-cream-100'
                  }`}
                >
                  <Upload className="w-5 h-5" />
                  <span className="font-medium">Upload Documents</span>
                  {uploadedDocuments.length > 0 && (
                    <span className="ml-auto bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                      {uploadedDocuments.length}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setActiveTab('portfolio')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === 'portfolio'
                      ? 'bg-primary-700 text-white'
                      : 'text-gray-700 hover:bg-cream-100'
                  }`}
                >
                  <PieChartIcon className="w-5 h-5" />
                  <span className="font-medium">Portfolio</span>
                </button>
              </nav>
            </div>

            {/* Quick Info */}
            <div className="card hidden lg:block">
              <h3 className="text-lg font-bold mb-3 text-primary-700">Your Profile</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Age:</span>
                  <span className="font-semibold">{profile.age}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Retirement Age:</span>
                  <span className="font-semibold">{profile.retirementAge}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Risk Tolerance:</span>
                  <span className="font-semibold capitalize">{profile.riskTolerance}</span>
                </div>
                <div className="pt-2 border-t border-cream-300">
                  <p className="text-gray-600">Goal:</p>
                  <p className="font-medium mt-1">{profile.investmentGoal}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2">
            <div className="card h-[calc(100vh-200px)] overflow-hidden">

              {/* Chat - keep mounted to preserve sources */}
              <div className={activeTab === 'chat' ? 'block h-full' : 'hidden'}>
                <ChatInterface sessionId={sessionId} />
              </div>

              {/* Upload - conditional render is fine */}
              {activeTab === 'upload' && (
                <div className="h-full overflow-y-auto">
                  <DocumentUpload
                    sessionId={sessionId}
                    onDocumentsChange={handleDocumentsChange}
                  />
                </div>
              )}

              {/* Portfolio - conditional render so it fetches fresh data each time */}
              {activeTab === 'portfolio' && (
                <div className="h-full overflow-y-auto p-4 space-y-6">
                  <MarketOverview />
                  <LivePortfolio sessionId={sessionId} />
                  <div className="pt-4 border-t border-cream-300">
                    <h3 className="font-bold mb-3 text-primary-700">Recommended Allocation</h3>
                    <PortfolioRecommendation profile={profile} />
                  </div>
                </div>
              )}

            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
