import { useState } from 'react';
import { LogOut, User, MessageSquare, Upload, PieChart as PieChartIcon } from 'lucide-react';
import ChatInterface from '../components/ChatInterface';
import DocumentUpload from '../components/DocumentUpload';
import PortfolioRecommendation from '../components/PortfolioRecommendation';
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

  const handleDocumentUpload = (document: Document) => {
    setUploadedDocuments((prev) => [...prev, document]);
    // Switch to chat tab after successful upload
    setActiveTab('chat');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-8 h-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">FinWhiz</h1>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-lg">
                <User className="w-5 h-5 text-gray-600" />
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">Age {profile.age}</p>
                  <p className="text-xs text-gray-600">Retires at {profile.retirementAge}</p>
                </div>
              </div>
              <button
                onClick={onLogout}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
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
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <MessageSquare className="w-5 h-5" />
                  <span className="font-medium">Chat</span>
                </button>

                <button
                  onClick={() => setActiveTab('upload')}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    activeTab === 'upload'
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
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
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <PieChartIcon className="w-5 h-5" />
                  <span className="font-medium">Portfolio</span>
                </button>
              </nav>
            </div>

            {/* Quick Info */}
            <div className="card hidden lg:block">
              <h3 className="text-lg font-bold mb-3">Your Profile</h3>
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
                <div className="pt-2 border-t border-gray-200">
                  <p className="text-gray-600">Goal:</p>
                  <p className="font-medium mt-1">{profile.investmentGoal}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2">
            <div className="card h-[calc(100vh-200px)]">
              {activeTab === 'chat' && <ChatInterface sessionId={sessionId} />}
              {activeTab === 'upload' && (
                <div className="overflow-y-auto h-full">
                  <DocumentUpload sessionId={sessionId} onUploadComplete={handleDocumentUpload} />
                </div>
              )}
              {activeTab === 'portfolio' && (
                <div className="overflow-y-auto h-full">
                  <PortfolioRecommendation profile={profile} />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
