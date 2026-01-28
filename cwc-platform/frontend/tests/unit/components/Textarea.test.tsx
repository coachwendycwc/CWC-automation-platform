import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Textarea } from '@/components/ui/textarea'

describe('Textarea', () => {
  it('renders correctly', () => {
    render(<Textarea placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('accepts user input', async () => {
    const user = userEvent.setup()
    render(<Textarea data-testid="textarea" />)

    const textarea = screen.getByTestId('textarea')
    await user.type(textarea, 'Hello World')

    expect(textarea).toHaveValue('Hello World')
  })

  it('supports controlled value', () => {
    render(<Textarea value="Controlled text" onChange={() => {}} data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveValue('Controlled text')
  })

  it('can be disabled', () => {
    render(<Textarea disabled data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toBeDisabled()
  })

  it('applies custom className', () => {
    render(<Textarea className="custom-class" data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveClass('custom-class')
  })

  it('supports rows attribute', () => {
    render(<Textarea rows={5} data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveAttribute('rows', '5')
  })

  it('supports name attribute', () => {
    render(<Textarea name="message" data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveAttribute('name', 'message')
  })

  it('supports required attribute', () => {
    render(<Textarea required data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toBeRequired()
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Textarea ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLTextAreaElement)
  })

  it('has default styling', () => {
    render(<Textarea data-testid="textarea" />)
    const textarea = screen.getByTestId('textarea')
    expect(textarea).toHaveClass('flex', 'min-h-[80px]', 'w-full')
  })

  it('handles onChange event', async () => {
    const user = userEvent.setup()
    let value = ''
    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      value = e.target.value
    }

    render(<Textarea onChange={handleChange} data-testid="textarea" />)
    await user.type(screen.getByTestId('textarea'), 'Test')

    expect(value).toBe('Test')
  })

  it('supports maxLength', () => {
    render(<Textarea maxLength={100} data-testid="textarea" />)
    expect(screen.getByTestId('textarea')).toHaveAttribute('maxLength', '100')
  })

  it('supports placeholder', () => {
    render(<Textarea placeholder="Type here..." />)
    expect(screen.getByPlaceholderText('Type here...')).toBeInTheDocument()
  })
})
