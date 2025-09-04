import '@testing-library/jest-dom';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      refresh: jest.fn(),
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return '/';
  },
}));

// Mock Next.js image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props) => {
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...props} />;
  },
}));

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8001';
process.env.NEXT_PUBLIC_SESSION_ID = '1';
process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID = 'test-google-client-id';

// Mock Google OAuth
jest.mock('@react-oauth/google', () => ({
  GoogleOAuthProvider: ({ children }) => children,
  GoogleLogin: ({ onSuccess, onError }) => (
    <button
      data-testid="google-login-button"
      onClick={() => onSuccess?.({ credential: 'mock-credential' })}
    >
      Sign in with Google
    </button>
  ),
}));

// Setup fetch mock
global.fetch = jest.fn();