import { useState, useEffect } from 'react';
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
      console.log('Creating session for user:', userId);

      // Create session with backend
      const newSession = await api.createSession(userId);
      console.log('Session created:', newSession);

      setProfile(userProfile);
      setSession(newSession);

      // Store in localStorage for persistence
      localStorage.setItem('finwhiz_profile', JSON.stringify(userProfile));
      localStorage.setItem('finwhiz_session', JSON.stringify(newSession));
      console.log('Session saved to localStorage');
    } catch (error) {
      console.error('Error creating session:', error);
      console.error('Error details:', error);
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
    const validateSession = async () => {
      console.log('Checking for saved session...');
      const savedProfile = localStorage.getItem('finwhiz_profile');
      const savedSession = localStorage.getItem('finwhiz_session');

      console.log('Saved profile:', savedProfile);
      console.log('Saved session:', savedSession);

      if (savedProfile && savedSession) {
        try {
          const parsedProfile = JSON.parse(savedProfile);
          const parsedSession = JSON.parse(savedSession);

          console.log('Parsed profile:', parsedProfile);
          console.log('Parsed session:', parsedSession);
          console.log('Session ID will be:', parsedSession.id);

          // Validate session still exists on backend
          if (parsedSession.id) {
            try {
              console.log('Validating session with backend...');
              await api.getSessionContext(parsedSession.id);
              console.log('Session is valid!');

              setProfile(parsedProfile);
              setSession(parsedSession);
            } catch (validationError) {
              console.warn('Session no longer valid on backend, clearing...', validationError);
              localStorage.removeItem('finwhiz_profile');
              localStorage.removeItem('finwhiz_session');
            }
          } else {
            console.warn('Session missing id, clearing...');
            localStorage.removeItem('finwhiz_profile');
            localStorage.removeItem('finwhiz_session');
          }
        } catch (error) {
          console.error('Error parsing saved data:', error);
          localStorage.removeItem('finwhiz_profile');
          localStorage.removeItem('finwhiz_session');
        }
      } else {
        console.log('No saved session found');
      }
    };

    validateSession();
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

  console.log('Rendering Dashboard with session:', session);
  console.log('Session ID being passed:', session.id);

  return <Dashboard profile={profile} sessionId={session.id} onLogout={handleLogout} />;
}

export default App;
