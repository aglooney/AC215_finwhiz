import React, { useState, useEffect } from 'react';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import { api } from './services/api';
import type { UserProfile, Session } from './types';
import { Loader2 } from 'lucide-react';

function App() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleOnboardingComplete = async (userProfile: UserProfile) => {
    setIsLoading(true);
    try {
      // Generate a unique user ID
      const userId = crypto.randomUUID();

      // Create session with backend
      const newSession = await api.createSession(userId);

      setProfile(userProfile);
      setSession(newSession);

      // Store in localStorage for persistence
      localStorage.setItem('finwhiz_profile', JSON.stringify(userProfile));
      localStorage.setItem('finwhiz_session', JSON.stringify(newSession));
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Failed to initialize session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setProfile(null);
    setSession(null);
    localStorage.removeItem('finwhiz_profile');
    localStorage.removeItem('finwhiz_session');
  };

  // Check for existing session on mount
  useEffect(() => {
    const savedProfile = localStorage.getItem('finwhiz_profile');
    const savedSession = localStorage.getItem('finwhiz_session');

    if (savedProfile && savedSession) {
      try {
        setProfile(JSON.parse(savedProfile));
        setSession(JSON.parse(savedSession));
      } catch (error) {
        console.error('Error parsing saved data:', error);
        localStorage.removeItem('finwhiz_profile');
        localStorage.removeItem('finwhiz_session');
      }
    }
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Setting up your session...</p>
        </div>
      </div>
    );
  }

  if (!profile || !session) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return <Dashboard profile={profile} sessionId={session.session_id} onLogout={handleLogout} />;
}

export default App;
