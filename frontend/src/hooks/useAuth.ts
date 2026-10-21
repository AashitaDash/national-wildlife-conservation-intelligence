import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

/**
 * Convenience hook for consuming the AuthContext.
 * Kept in its own file so Vite Fast Refresh can handle AuthContext.tsx
 * (which exports a component) and this hook file independently.
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
