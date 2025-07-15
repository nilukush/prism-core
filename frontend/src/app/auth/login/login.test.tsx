import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useRouter } from 'next/navigation'
import { signIn } from 'next-auth/react'
import LoginPage from './page'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(() => new URLSearchParams()),
}))

jest.mock('next-auth/react', () => ({
  signIn: jest.fn(),
}))

// Mock the providers component
jest.mock('@/components/providers', () => ({
  __esModule: true,
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

describe('LoginPage', () => {
  const mockPush = jest.fn()
  const mockRouter = {
    push: mockPush,
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
  })

  it('renders login form', () => {
    render(<LoginPage />)

    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
  })

  it('displays validation errors for empty fields', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument()
      expect(screen.getByText(/password is required/i)).toBeInTheDocument()
    })
  })

  it('displays validation error for invalid email', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    await user.type(emailInput, 'invalid-email')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid email address/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid credentials', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockResolvedValueOnce({
      ok: true,
      error: null,
      status: 200,
      url: null,
    })

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(signIn).toHaveBeenCalledWith('credentials', {
        email: 'test@example.com',
        password: 'password123',
        redirect: false,
      })
    })

    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('displays error message on login failure', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockResolvedValueOnce({
      ok: false,
      error: 'Invalid credentials',
      status: 401,
      url: null,
    })

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'wrongpassword')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('disables submit button while loading', async () => {
    const user = userEvent.setup()
    ;(signIn as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    )

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    expect(submitButton).toBeDisabled()
    expect(screen.getByText(/signing in/i)).toBeInTheDocument()
  })

  it('redirects to callback URL after successful login', async () => {
    const user = userEvent.setup()
    const callbackUrl = '/app/projects'
    
    // Mock useSearchParams to return callback URL
    jest.mocked(useRouter).mockReturnValue({
      ...mockRouter,
      query: { callbackUrl },
    })

    ;(signIn as jest.Mock).mockResolvedValueOnce({
      ok: true,
      error: null,
      status: 200,
      url: null,
    })

    render(<LoginPage />)

    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')

    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(callbackUrl)
    })
  })

  it('shows password visibility toggle', async () => {
    const user = userEvent.setup()
    render(<LoginPage />)

    const passwordInput = screen.getByLabelText(/password/i)
    const toggleButton = screen.getByRole('button', { name: /show password/i })

    // Initially password input should be of type password
    expect(passwordInput).toHaveAttribute('type', 'password')

    // Click toggle to show password
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'text')

    // Click toggle to hide password again
    await user.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })
})