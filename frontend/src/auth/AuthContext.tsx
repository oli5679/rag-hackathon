import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import type { User, Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signInWithMagicLink: (email: string) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<{ error: AuthError | null }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Timeout safety valve
  const timeoutTimer = setTimeout(() => {
    console.warn('[Auth] Session check timed out. Forcing loading=false. CHECK ENV VARS.');
    setLoading(false);
  }, 4000);

  // Get initial session
  supabase.auth.getSession().then(({ data: { session } }) => {
    clearTimeout(timeoutTimer);
    console.log('[Auth] Session loaded:', session?.user?.id);
    setSession(session);
    setUser(session?.user ?? null);
    setLoading(false);
  }).catch(err => {
    clearTimeout(timeoutTimer);
    console.error('[Auth] Failed to get session:', err);
    setLoading(false);
  });

  // Listen for auth changes
  const { data: { subscription } } = supabase.auth.onAuthStateChange(
    async (_event, session) => {
      console.log('[Auth] Auth state changed:', _event, session?.user?.id);
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    }
  );

  return () => subscription.unsubscribe();
}, []);

const signInWithMagicLink = async (email: string) => {
  const redirectUrl = import.meta.env.VITE_APP_URL || window.location.origin;
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: redirectUrl }
  });
  return { error };
};

const signOut = async () => {
  const { error } = await supabase.auth.signOut();
  return { error };
};

const value: AuthContextType = {
  user,
  session,
  loading,
  signInWithMagicLink,
  signOut,
};

return (
  <AuthContext.Provider value={value}>
    {children}
  </AuthContext.Provider>
);
}
