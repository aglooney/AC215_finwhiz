import { useState, useEffect } from 'react';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import { Login } from './components/Login';
import { Signup } from './components/Signup';
import { useAuth } from './contexts/AuthContext';
import { api } from './services/api';
import type { UserProfile, Session } from './types';
import { Loader2 } from 'lucide-react';

function App() {
  const { loading: authLoading, logout: authLogout, isAuthenticated } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSignup, setShowSignup] = useState(false);

  const handleOnboardingComplete = async (userProfile: UserProfile) => {
    setIsLoading(true);
    try {
      console.log('Creating session for authenticated user');

      // Create session with backend (user authentication handled by JWT)
      const newSession = await api.createSession();
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
    authLogout();
    setProfile(null);
    setSession(null);
    localStorage.removeItem('finwhiz_profile');
    localStorage.removeItem('finwhiz_session');
  };

  // Load user data from backend on mount when authenticated
  useEffect(() => {
    const loadUserData = async () => {
      if (!isAuthenticated) {
        console.log('Not authenticated, skipping profile load');
        return;
      }

      setIsLoading(true);
      try {
        console.log('Loading profile from backend...');

        // Fetch profile from backend
        const backendProfile = await api.getProfile();

        if (backendProfile) {
          console.log('Profile loaded from backend:', backendProfile);

          // Convert backend format to frontend format
          const profile: UserProfile = {
            age: backendProfile.age!,
            retirementAge: backendProfile.retirement_age!,
            riskTolerance: backendProfile.risk_tolerance as 'conservative' | 'moderate' | 'aggressive',
            investmentGoal: backendProfile.investment_goal!,
          };
          setProfile(profile);

          // Cache in localStorage
          localStorage.setItem('finwhiz_profile', JSON.stringify(profile));

          // Load or create session
          const savedSession = localStorage.getItem('finwhiz_session');
          if (savedSession) {
            try {
              const parsedSession = JSON.parse(savedSession);
              // Validate session still exists on backend
              await api.getSessionContext(parsedSession.id);
              console.log('Existing session is valid');
              setSession(parsedSession);
            } catch (validationError) {
              console.warn('Session no longer valid, creating new one...', validationError);
              const newSession = await api.createSession();
              setSession(newSession);
              localStorage.setItem('finwhiz_session', JSON.stringify(newSession));
            }
          } else {
            console.log('No saved session, creating new one...');
            const newSession = await api.createSession();
            setSession(newSession);
            localStorage.setItem('finwhiz_session', JSON.stringify(newSession));
          }
        } else {
          console.log('No profile found, user needs to complete onboarding');
          // Clear any stale localStorage data
          localStorage.removeItem('finwhiz_profile');
          localStorage.removeItem('finwhiz_session');
        }
      } catch (error) {
        console.error('Failed to load user data:', error);
        // Clear localStorage on error
        localStorage.removeItem('finwhiz_profile');
        localStorage.removeItem('finwhiz_session');
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, [isAuthenticated]);

  // Show loading spinner while checking authentication
  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">
            {isLoading ? 'Setting up your session...' : 'Loading...'}
          </p>
        </div>
      </div>
    );
  }

  // Show Login/Signup if not authenticated
  if (!isAuthenticated) {
    return showSignup ? (
      <Signup onSwitchToLogin={() => setShowSignup(false)} />
    ) : (
      <Login onSwitchToSignup={() => setShowSignup(true)} />
    );
  }

  // Show Onboarding if authenticated but no profile/session
  if (!profile || !session) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  // Show Dashboard if authenticated and has profile/session
  console.log('Rendering Dashboard with session:', session);
  console.log('Session ID being passed:', session.id);

  return <Dashboard profile={profile} sessionId={session.id} onLogout={handleLogout} />;
}

export default App;
