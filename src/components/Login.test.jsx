import { render } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import { AuthContext } from '../context/AuthContext';

// Mock values for context
const mockContext = {
  login: vi.fn(),
  isAuthenticated: false,
  loading: false
};

test('Login component matches snapshot', () => {
  const { asFragment } = render(
    <AuthContext.Provider value={mockContext}>
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    </AuthContext.Provider>
  );
  expect(asFragment()).toMatchSnapshot();
});
