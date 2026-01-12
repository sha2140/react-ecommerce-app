import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock useNavigate and provide BrowserRouter
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
})

// Mock AuthContext
vi.mock('../context/AuthContext', async () => {
  const React = await import('react');
  const AuthContext = React.createContext();
  return {
    AuthContext,
    useAuth: () => ({
      login: vi.fn(),
      isAuthenticated: false,
      loading: false,
    }),
  };
})
