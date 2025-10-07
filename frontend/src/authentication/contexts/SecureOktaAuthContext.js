import React, { createContext, useContext, useEffect, useState } from 'react';

const SecureOktaAuthContext = createContext();

export const useSecureOktaAuth = () => {
  const context = useContext(SecureOktaAuthContext);
  if (!context) {
    throw new Error('useSecureOktaAuth must be used within SecureOktaProvider');
  }
  return context;
};

export const SecureOktaProvider = ({ children, config }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/status', {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateCodeVerifier = () => {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return btoa(String.fromCharCode.apply(null, array))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  };

  const generateCodeChallenge = async (verifier) => {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const digest = await crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(digest)))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  };

  const generateState = () => {
    return (
      Math.random().toString(36).substring(2, 15) +
      Math.random().toString(36).substring(2, 15)
    );
  };

  const login = async () => {
    try {
      const codeVerifier = generateCodeVerifier();
      const codeChallenge = await generateCodeChallenge(codeVerifier);
      const state = generateState();

      sessionStorage.setItem('code_verifier', codeVerifier);
      sessionStorage.setItem('auth_state', state);

      const params = new URLSearchParams({
        client_id: config.clientId,
        response_type: 'code',
        scope: 'openid profile email',
        redirect_uri:
          'https://d2laxidvw6d439.cloudfront.net/auth/callback',
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256'
      });

      window.location.href = `${config.issuer}/v1/authorize?${params}`;
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setUser(null);
      setIsAuthenticated(false);
      sessionStorage.removeItem('code_verifier');
      sessionStorage.removeItem('auth_state');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout
  };

  return (
    <SecureOktaAuthContext.Provider value={value}>
      {children}
    </SecureOktaAuthContext.Provider>
  );
};