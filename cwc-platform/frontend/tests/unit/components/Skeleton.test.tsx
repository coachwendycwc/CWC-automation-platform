import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton } from '@/components/ui/skeleton'

describe('Skeleton', () => {
  it('renders correctly', () => {
    render(<Skeleton data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton')).toBeInTheDocument()
  })

  it('has animation class', () => {
    render(<Skeleton data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton')).toHaveClass('animate-pulse')
  })

  it('has background styling', () => {
    render(<Skeleton data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton')).toHaveClass('bg-gray-200')
  })

  it('has rounded styling', () => {
    render(<Skeleton data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton')).toHaveClass('rounded-md')
  })

  it('applies custom className', () => {
    render(<Skeleton className="h-4 w-full" data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('h-4', 'w-full')
  })

  it('can set custom dimensions', () => {
    render(<Skeleton className="h-10 w-10" data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('h-10', 'w-10')
  })

  it('renders as div by default', () => {
    render(<Skeleton data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton').tagName).toBe('DIV')
  })

  it('can be used for text placeholders', () => {
    render(<Skeleton className="h-4 w-[250px]" data-testid="skeleton" />)
    expect(screen.getByTestId('skeleton')).toBeInTheDocument()
  })

  it('can be used for avatar placeholders', () => {
    render(<Skeleton className="h-12 w-12 rounded-full" data-testid="skeleton" />)
    const skeleton = screen.getByTestId('skeleton')
    expect(skeleton).toHaveClass('rounded-full')
  })

  it('can be composed for card placeholders', () => {
    render(
      <div className="space-y-2">
        <Skeleton className="h-4 w-[250px]" data-testid="skeleton-1" />
        <Skeleton className="h-4 w-[200px]" data-testid="skeleton-2" />
      </div>
    )
    expect(screen.getByTestId('skeleton-1')).toBeInTheDocument()
    expect(screen.getByTestId('skeleton-2')).toBeInTheDocument()
  })
})
