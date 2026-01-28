import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/badge'

describe('Badge', () => {
  it('renders children correctly', () => {
    render(<Badge>New</Badge>)
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('renders default variant', () => {
    render(<Badge data-testid="badge">Default</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('bg-primary')
  })

  it('renders secondary variant', () => {
    render(<Badge variant="secondary" data-testid="badge">Secondary</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('bg-secondary')
  })

  it('renders destructive variant', () => {
    render(<Badge variant="destructive" data-testid="badge">Error</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('bg-destructive')
  })

  it('renders outline variant', () => {
    render(<Badge variant="outline" data-testid="badge">Outline</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('text-foreground')
  })

  it('applies custom className', () => {
    render(<Badge className="custom-class" data-testid="badge">Custom</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('custom-class')
  })

  it('renders as inline-flex', () => {
    render(<Badge data-testid="badge">Flex</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('inline-flex')
  })

  it('has rounded styling', () => {
    render(<Badge data-testid="badge">Rounded</Badge>)
    expect(screen.getByTestId('badge')).toHaveClass('rounded-full')
  })

  it('renders with multiple children', () => {
    render(
      <Badge>
        <span>Icon</span>
        <span>Text</span>
      </Badge>
    )
    expect(screen.getByText('Icon')).toBeInTheDocument()
    expect(screen.getByText('Text')).toBeInTheDocument()
  })
})
