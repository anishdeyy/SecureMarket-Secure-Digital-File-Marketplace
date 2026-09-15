'use client';
import React, { createContext, useContext, useEffect, useState } from 'react';
import api from './api';

interface User {
  id: string; email: string; username: string; full_name?: string;
  role?: string; roles: string; is_email_verified: boolean; is_suspended: boolean; seller_approved: boolean;
}
interface AuthCtx {
  user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>;
  logout: () => void; register: (data: any) => Promise<void>; refreshUser: () => Promise<void>;
  isAdmin: () => boolean; isSeller: () => boolean; isBuyer: () => boolean;
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      api.get('/api/auth/me').then(r => setUser(r.data)).catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
      }).finally(() => setLoading(false));
    } else setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/api/auth/login', { email, password });
    localStorage.setItem('access_token', data.access_token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    window.location.href = '/';
  };

  const register = async (formData: any) => {
    const { data } = await api.post('/api/auth/register', formData);
    localStorage.setItem('access_token', data.access_token);
    setUser(data.user);
  };

  const refreshUser = async () => {
    const { data } = await api.get('/api/auth/me');
    setUser(data);
  };

  const getRole = (): string => {
    if (!user) return '';
    const r = (user.role || user.roles || 'BUYER').toUpperCase().trim();
    if (r.includes('ADMIN')) return 'ADMIN';
    if (r.includes('SELLER')) return 'SELLER';
    return 'BUYER';
  };

  const isAdmin = () => getRole() === 'ADMIN';
  const isSeller = () => getRole() === 'SELLER';
  const isBuyer = () => getRole() === 'BUYER';

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, refreshUser, isAdmin, isSeller, isBuyer }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
