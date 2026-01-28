import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Checkbox } from '@/components/ui/checkbox'

describe('Checkbox', () => {
  it('renders correctly', () => {
    render(<Checkbox aria-label="Accept terms" />)
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('is unchecked by default', () => {
    render(<Checkbox aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).not.toBeChecked()
  })

  it('can be checked by default', () => {
    render(<Checkbox checked aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toBeChecked()
  })

  it('toggles on click', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<Checkbox onCheckedChange={onChange} aria-label="Accept" />)

    await user.click(screen.getByRole('checkbox'))
    expect(onChange).toHaveBeenCalledWith(true)
  })

  it('can be disabled', () => {
    render(<Checkbox disabled aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toBeDisabled()
  })

  it('applies custom className', () => {
    render(<Checkbox className="custom-class" aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toHaveClass('custom-class')
  })

  it('supports id attribute', () => {
    render(<Checkbox id="terms-checkbox" aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toHaveAttribute('id', 'terms-checkbox')
  })

  it('renders with name prop', () => {
    // Radix Checkbox uses internal state for name
    render(<Checkbox name="terms" aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Checkbox ref={ref} aria-label="Accept" />)
    expect(ref.current).not.toBeNull()
  })

  it('supports required attribute', () => {
    render(<Checkbox required aria-label="Accept" />)
    expect(screen.getByRole('checkbox')).toBeRequired()
  })

  it('works with label', () => {
    render(
      <div>
        <Checkbox id="accept" aria-label="Accept terms" />
        <label htmlFor="accept">Accept terms and conditions</label>
      </div>
    )
    expect(screen.getByText('Accept terms and conditions')).toBeInTheDocument()
  })

  it('has proper styling', () => {
    render(<Checkbox aria-label="Accept" />)
    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toHaveClass('h-4', 'w-4')
  })
})
