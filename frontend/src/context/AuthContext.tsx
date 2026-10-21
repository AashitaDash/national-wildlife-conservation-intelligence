import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, RoleName } from '../types';
import { authService } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  register: (userData: { username: string; email: string; password: string; full_name?: string }) => Promise<void>;
  logout: () => void;
  hasRole: (roles: RoleName | RoleName[]) => boolean;
  primaryRole: RoleName;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (err) {
          console.error('Failed to fetch authenticated user:', err);
          logout();
        }
      }
      setLoading(false);
    };

    fetchUser();
  }, [token]);

  const login = async (username: string, password: string): Promise<User> => {
    const res = await authService.login(username, password);
    localStorage.setItem('token', res.access_token);
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  };

  const register = async (userData: { username: string; email: string; password: string; full_name?: string }) => {
    const res = await authService.register(userData);
    // Backend returns an empty access_token on register (user must login separately).
    // Do NOT store an empty token — that would trigger a getCurrentUser() call with
    // an empty Bearer header and immediately kick off a logout() loop.
    if (res.access_token) {
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
    }
    // If no token returned, just let the caller redirect to /login
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const hasRole = (roles: RoleName | RoleName[]): boolean => {
    if (!user || !user.roles) return false;
    const requiredRoles = Array.isArray(roles) ? roles : [roles];
    const userRoleNames = user.roles.map((r) => r.name);
    // ADMIN has full access
    if (userRoleNames.includes('ADMIN')) return true;
    return requiredRoles.some((role) => userRoleNames.includes(role));
  };

  const primaryRole: RoleName = user && user.roles.length > 0 ? user.roles[0].name : 'CITIZEN';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        hasRole,
        primaryRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
