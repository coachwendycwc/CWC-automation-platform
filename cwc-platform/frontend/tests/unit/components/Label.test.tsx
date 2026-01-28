import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Label } from '@/components/ui/label'

describe('Label', () => {
  it('renders text correctly', () => {
    render(<Label>Username</Label>)
    expect(screen.getByText('Username')).toBeInTheDocument()
  })

  it('renders as label element', () => {
    render(<Label>Email</Label>)
    const label = screen.getByText('Email')
    expect(label.tagName).toBe('LABEL')
  })

  it('supports htmlFor attribute', () => {
    render(<Label htmlFor="email-input">Email</Label>)
    expect(screen.getByText('Email')).toHaveAttribute('for', 'email-input')
  })

  it('applies custom className', () => {
    render(<Label className="custom-class" data-testid="label">Test</Label>)
    expect(screen.getByTestId('label')).toHaveClass('custom-class')
  })

  it('has default font styling', () => {
    render(<Label data-testid="label">Test</Label>)
    expect(screen.getByTestId('label')).toHaveClass('text-sm', 'font-medium')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Label ref={ref}>Test</Label>)
    expect(ref.current).toBeInstanceOf(HTMLLabelElement)
  })

  it('renders with children elements', () => {
    render(
      <Label>
        <span>Required</span>
        <span className="text-red-500">*</span>
      </Label>
    )
    expect(screen.getByText('Required')).toBeInTheDocument()
    expect(screen.getByText('*')).toBeInTheDocument()
  })

  it('supports aria attributes', () => {
    render(<Label aria-label="Name field" data-testid="label">Name</Label>)
    expect(screen.getByTestId('label')).toHaveAttribute('aria-label', 'Name field')
  })
})
