import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Input } from '@/components/ui/input'

describe('Input', () => {
  it('renders input element', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders with placeholder', () => {
    render(<Input placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('handles text input', async () => {
    const user = userEvent.setup()
    render(<Input />)
    const input = screen.getByRole('textbox')
    await user.type(input, 'Hello World')
    expect(input).toHaveValue('Hello World')
  })

  it('calls onChange handler', async () => {
    const handleChange = vi.fn()
    const user = userEvent.setup()
    render(<Input onChange={handleChange} />)
    const input = screen.getByRole('textbox')
    await user.type(input, 'Test')
    expect(handleChange).toHaveBeenCalled()
  })

  it('can be disabled', () => {
    render(<Input disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('renders with type password', () => {
    render(<Input type="password" data-testid="password-input" />)
    expect(screen.getByTestId('password-input')).toHaveAttribute('type', 'password')
  })

  it('renders with type email', () => {
    render(<Input type="email" data-testid="email-input" />)
    expect(screen.getByTestId('email-input')).toHaveAttribute('type', 'email')
  })

  it('renders with custom className', () => {
    render(<Input className="custom-input" />)
    expect(screen.getByRole('textbox')).toHaveClass('custom-input')
  })

  it('forwards ref to input element', () => {
    const ref = vi.fn()
    render(<Input ref={ref} />)
    expect(ref).toHaveBeenCalled()
  })

  it('displays value when controlled', () => {
    render(<Input value="Controlled Value" onChange={() => {}} />)
    expect(screen.getByRole('textbox')).toHaveValue('Controlled Value')
  })

  it('applies focus styles on focus', async () => {
    const user = userEvent.setup()
    render(<Input />)
    const input = screen.getByRole('textbox')
    await user.click(input)
    expect(input).toHaveFocus()
  })
})
