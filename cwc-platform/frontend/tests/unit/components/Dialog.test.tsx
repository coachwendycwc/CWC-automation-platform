import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from '@/components/ui/dialog'

describe('Dialog', () => {
  describe('Dialog Root', () => {
    it('renders trigger and opens dialog on click', async () => {
      render(
        <Dialog>
          <DialogTrigger>Open Dialog</DialogTrigger>
          <DialogContent>
            <DialogTitle>Test Dialog</DialogTitle>
            <DialogDescription>Dialog description</DialogDescription>
          </DialogContent>
        </Dialog>
      )

      const trigger = screen.getByText('Open Dialog')
      expect(trigger).toBeInTheDocument()

      fireEvent.click(trigger)

      // Dialog content should be visible after clicking trigger
      expect(await screen.findByText('Test Dialog')).toBeInTheDocument()
      expect(screen.getByText('Dialog description')).toBeInTheDocument()
    })

    it('renders as controlled component', () => {
      const onOpenChange = vi.fn()

      render(
        <Dialog open={true} onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogTitle>Controlled Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      expect(screen.getByText('Controlled Dialog')).toBeInTheDocument()
    })

    it('renders as closed when open is false', () => {
      render(
        <Dialog open={false}>
          <DialogContent>
            <DialogTitle>Hidden Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      expect(screen.queryByText('Hidden Dialog')).not.toBeInTheDocument()
    })
  })

  describe('DialogTrigger', () => {
    it('renders as button by default', () => {
      render(
        <Dialog>
          <DialogTrigger>Click me</DialogTrigger>
          <DialogContent>
            <DialogTitle>Content</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      const trigger = screen.getByText('Click me')
      expect(trigger).toBeInTheDocument()
    })

    it('renders asChild when prop is set', () => {
      render(
        <Dialog>
          <DialogTrigger asChild>
            <span data-testid="custom-trigger">Custom Trigger</span>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Content</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      expect(screen.getByTestId('custom-trigger')).toBeInTheDocument()
    })
  })

  describe('DialogContent', () => {
    it('renders children content', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <p>Dialog body content</p>
          </DialogContent>
        </Dialog>
      )

      expect(await screen.findByText('Dialog body content')).toBeInTheDocument()
    })

    it('applies custom className', async () => {
      render(
        <Dialog open={true}>
          <DialogContent className="custom-class" data-testid="dialog-content">
            <DialogTitle>Test</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      const content = await screen.findByRole('dialog')
      expect(content).toHaveClass('custom-class')
    })

    it('renders close button', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Test</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      const closeButton = await screen.findByRole('button', { name: /close/i })
      expect(closeButton).toBeInTheDocument()
    })
  })

  describe('DialogHeader', () => {
    it('renders with default styles', () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogHeader data-testid="dialog-header">
              <DialogTitle>Header Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      )

      const header = screen.getByTestId('dialog-header')
      expect(header).toBeInTheDocument()
      expect(header).toHaveClass('flex', 'flex-col')
    })

    it('applies custom className', () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogHeader className="custom-header" data-testid="dialog-header">
              <DialogTitle>Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      )

      const header = screen.getByTestId('dialog-header')
      expect(header).toHaveClass('custom-header')
    })
  })

  describe('DialogFooter', () => {
    it('renders with default styles', () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogFooter data-testid="dialog-footer">
              <button>Cancel</button>
              <button>Confirm</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      const footer = screen.getByTestId('dialog-footer')
      expect(footer).toBeInTheDocument()
      expect(footer).toHaveClass('flex')
    })

    it('renders children buttons', () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogFooter>
              <button>Cancel</button>
              <button>Confirm</button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )

      expect(screen.getByText('Cancel')).toBeInTheDocument()
      expect(screen.getByText('Confirm')).toBeInTheDocument()
    })
  })

  describe('DialogTitle', () => {
    it('renders with correct heading styles', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>My Dialog Title</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      const title = await screen.findByText('My Dialog Title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveClass('text-lg', 'font-semibold')
    })

    it('applies custom className', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle className="custom-title">Title</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      const title = await screen.findByText('Title')
      expect(title).toHaveClass('custom-title')
    })
  })

  describe('DialogDescription', () => {
    it('renders with muted foreground styling', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogDescription>This is a description</DialogDescription>
          </DialogContent>
        </Dialog>
      )

      const description = await screen.findByText('This is a description')
      expect(description).toBeInTheDocument()
      expect(description).toHaveClass('text-sm')
    })

    it('applies custom className', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogDescription className="custom-desc">Description</DialogDescription>
          </DialogContent>
        </Dialog>
      )

      const description = await screen.findByText('Description')
      expect(description).toHaveClass('custom-desc')
    })
  })

  describe('DialogClose', () => {
    it('closes dialog when clicked', async () => {
      const onOpenChange = vi.fn()

      render(
        <Dialog open={true} onOpenChange={onOpenChange}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogClose data-testid="close-btn">Close Dialog</DialogClose>
          </DialogContent>
        </Dialog>
      )

      const closeBtn = screen.getByTestId('close-btn')
      fireEvent.click(closeBtn)

      expect(onOpenChange).toHaveBeenCalledWith(false)
    })
  })

  describe('Accessibility', () => {
    it('has correct role', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Accessible Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      )

      expect(await screen.findByRole('dialog')).toBeInTheDocument()
    })

    it('associates title with dialog', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Dialog Title</DialogTitle>
            <DialogDescription>Dialog Description</DialogDescription>
          </DialogContent>
        </Dialog>
      )

      const dialog = await screen.findByRole('dialog')
      expect(dialog).toHaveAttribute('aria-describedby')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })
  })
})
