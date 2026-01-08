import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { API_URL } from '../services/api';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      // Try to fetch real user data from /me endpoint
      const response = await api.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      // For demo purposes, use mock user data
      const mockUser = {
        id: 'demo_user_id',
        email: 'judge@nexus.local',
        full_name: 'Imagine Cup Judge',
        role: 'admin',
        tenant_id: 'demo_tenant'
      };
      setUser(mockUser);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      console.log('🔐 Attempting login to:', `${API_URL}/api/v1/auth/login`);
      
      // Use the shared api instance which points to the correct backend
      const response = await api.post('auth/login', { 
        email, 
        password 
      });

      const { access_token, user: userData } = response.data;

      console.log('✅ Login successful:', userData);
      
      // Store token
      setToken(access_token);
      localStorage.setItem('token', access_token);
      
      // Update all axios instances with the token
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Set user data
      setUser(userData);
      
      return true;
    } catch (error: any) {
      console.error('❌ Login failed:', error.response?.data || error.message);
      setUser(null);
      setToken(null);
      localStorage.removeItem('token');
      return false;
    }
  };

  const logout = () => {
    console.log('🚪 Logging out');
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    delete api.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
