import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card'

describe('Card', () => {
  it('renders children correctly', () => {
    render(
      <Card>
        <div>Card Content</div>
      </Card>
    )
    expect(screen.getByText('Card Content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<Card className="custom-class" data-testid="card" />)
    expect(screen.getByTestId('card')).toHaveClass('custom-class')
  })

  it('forwards ref correctly', () => {
    const ref = { current: null }
    render(<Card ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLDivElement)
  })
})

describe('CardHeader', () => {
  it('renders children correctly', () => {
    render(
      <CardHeader>
        <span>Header Content</span>
      </CardHeader>
    )
    expect(screen.getByText('Header Content')).toBeInTheDocument()
  })

  it('applies default styles', () => {
    render(<CardHeader data-testid="header" />)
    expect(screen.getByTestId('header')).toHaveClass('flex', 'flex-col')
  })
})

describe('CardTitle', () => {
  it('renders as h3 by default', () => {
    render(<CardTitle>Title Text</CardTitle>)
    const title = screen.getByText('Title Text')
    expect(title.tagName).toBe('H3')
  })

  it('applies font styling', () => {
    render(<CardTitle data-testid="title">Title</CardTitle>)
    expect(screen.getByTestId('title')).toHaveClass('font-semibold')
  })
})

describe('CardDescription', () => {
  it('renders as p element', () => {
    render(<CardDescription>Description</CardDescription>)
    const desc = screen.getByText('Description')
    expect(desc.tagName).toBe('P')
  })

  it('applies muted text style', () => {
    render(<CardDescription data-testid="desc">Desc</CardDescription>)
    expect(screen.getByTestId('desc')).toHaveClass('text-muted-foreground')
  })
})

describe('CardContent', () => {
  it('renders children correctly', () => {
    render(
      <CardContent>
        <p>Content here</p>
      </CardContent>
    )
    expect(screen.getByText('Content here')).toBeInTheDocument()
  })

  it('applies padding', () => {
    render(<CardContent data-testid="content" />)
    expect(screen.getByTestId('content')).toHaveClass('p-6')
  })
})

describe('CardFooter', () => {
  it('renders children correctly', () => {
    render(
      <CardFooter>
        <button>Action</button>
      </CardFooter>
    )
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('applies flex layout', () => {
    render(<CardFooter data-testid="footer" />)
    expect(screen.getByTestId('footer')).toHaveClass('flex', 'items-center')
  })
})

describe('Card composition', () => {
  it('renders full card with all subcomponents', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Test Title</CardTitle>
          <CardDescription>Test description</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Main content</p>
        </CardContent>
        <CardFooter>
          <button>Submit</button>
        </CardFooter>
      </Card>
    )

    expect(screen.getByText('Test Title')).toBeInTheDocument()
    expect(screen.getByText('Test description')).toBeInTheDocument()
    expect(screen.getByText('Main content')).toBeInTheDocument()
    expect(screen.getByText('Submit')).toBeInTheDocument()
  })
})
