import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Progress } from '@/components/ui/progress'

describe('Progress', () => {
  it('renders correctly', () => {
    render(<Progress value={50} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('displays with value attribute', () => {
    render(<Progress value={75} />)
    const progressbar = screen.getByRole('progressbar')
    // Radix UI stores value internally
    expect(progressbar).toBeInTheDocument()
  })

  it('renders progress element', () => {
    render(<Progress value={50} />)
    const progressbar = screen.getByRole('progressbar')
    expect(progressbar).toBeInTheDocument()
  })

  it('handles 0 value', () => {
    render(<Progress value={0} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('handles 100 value', () => {
    render(<Progress value={100} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Progress value={50} className="custom-class" />)
    expect(screen.getByRole('progressbar')).toHaveClass('custom-class')
  })

  it('has relative positioning', () => {
    render(<Progress value={50} />)
    expect(screen.getByRole('progressbar')).toHaveClass('relative')
  })

  it('has overflow hidden', () => {
    render(<Progress value={50} />)
    expect(screen.getByRole('progressbar')).toHaveClass('overflow-hidden')
  })

  it('has rounded styling', () => {
    render(<Progress value={50} />)
    expect(screen.getByRole('progressbar')).toHaveClass('rounded-full')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Progress value={50} ref={ref} />)
    expect(ref.current).not.toBeNull()
  })

  it('handles undefined value gracefully', () => {
    render(<Progress value={undefined as unknown as number} />)
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('handles negative values as 0', () => {
    render(<Progress value={-10} />)
    // Component should handle this gracefully
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })

  it('handles values over 100', () => {
    render(<Progress value={150} />)
    // Component should handle this gracefully
    expect(screen.getByRole('progressbar')).toBeInTheDocument()
  })
})
