import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeToggle } from './theme-toggle'
import { useTheme } from 'next-themes'

// Mock next-themes
jest.mock('next-themes', () => ({
  useTheme: jest.fn(),
}))

describe('ThemeToggle', () => {
  const mockSetTheme = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useTheme as jest.Mock).mockReturnValue({
      theme: 'light',
      setTheme: mockSetTheme,
    })
  })

  it('renders the theme toggle button', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button', { name: /toggle theme/i })
    expect(button).toBeInTheDocument()
  })

  it('shows sun icon when theme is light', () => {
    render(<ThemeToggle />)
    const sunIcon = screen.getByTestId('sun-icon')
    expect(sunIcon).toBeInTheDocument()
  })

  it('shows moon icon when theme is dark', () => {
    ;(useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    })

    render(<ThemeToggle />)
    const moonIcon = screen.getByTestId('moon-icon')
    expect(moonIcon).toBeInTheDocument()
  })

  it('toggles theme from light to dark on click', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /toggle theme/i })
    await user.click(button)

    expect(mockSetTheme).toHaveBeenCalledWith('dark')
  })

  it('toggles theme from dark to light on click', async () => {
    const user = userEvent.setup()
    ;(useTheme as jest.Mock).mockReturnValue({
      theme: 'dark',
      setTheme: mockSetTheme,
    })

    render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /toggle theme/i })
    await user.click(button)

    expect(mockSetTheme).toHaveBeenCalledWith('light')
  })

  it('handles system theme', async () => {
    const user = userEvent.setup()
    ;(useTheme as jest.Mock).mockReturnValue({
      theme: 'system',
      setTheme: mockSetTheme,
    })

    render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /toggle theme/i })
    await user.click(button)

    // When theme is system, it should set to light
    expect(mockSetTheme).toHaveBeenCalledWith('light')
  })

  it('is keyboard accessible', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)

    const button = screen.getByRole('button', { name: /toggle theme/i })
    
    // Tab to focus the button
    await user.tab()
    expect(button).toHaveFocus()

    // Press Enter to toggle
    await user.keyboard('{Enter}')
    expect(mockSetTheme).toHaveBeenCalledWith('dark')

    // Press Space to toggle
    await user.keyboard(' ')
    expect(mockSetTheme).toHaveBeenCalledTimes(2)
  })
})