import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
  SelectGroup,
  SelectLabel,
  SelectSeparator,
} from '@/components/ui/select'

describe('Select', () => {
  describe('SelectTrigger', () => {
    it('renders with default styling', () => {
      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      expect(trigger).toBeInTheDocument()
      expect(trigger).toHaveClass('flex', 'h-10', 'w-full')
    })

    it('displays placeholder text', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Choose something" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Choose something')).toBeInTheDocument()
    })

    it('applies custom className', () => {
      render(
        <Select>
          <SelectTrigger className="custom-trigger" data-testid="select-trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      expect(trigger).toHaveClass('custom-trigger')
    })

    it('shows disabled state', () => {
      render(
        <Select disabled>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Disabled" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      expect(trigger).toBeDisabled()
    })

    it('has correct border styling', () => {
      render(
        <Select>
          <SelectTrigger data-testid="select-trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('select-trigger')
      expect(trigger).toHaveClass('border')
    })
  })

  describe('SelectValue', () => {
    it('displays selected value', () => {
      render(
        <Select defaultValue="option2">
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectItem value="option2">Selected Option</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Selected Option')).toBeInTheDocument()
    })

    it('shows placeholder when no value', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Pick one" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="a">A</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Pick one')).toBeInTheDocument()
    })
  })

  describe('Select controlled mode', () => {
    it('works as controlled component', () => {
      const onValueChange = vi.fn()

      render(
        <Select value="controlled" onValueChange={onValueChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="controlled">Controlled Value</SelectItem>
            <SelectItem value="other">Other</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Controlled Value')).toBeInTheDocument()
    })

    it('displays value from value prop', () => {
      render(
        <Select value="specific">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="specific">Specific Value</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByText('Specific Value')).toBeInTheDocument()
    })
  })

  describe('SelectItem', () => {
    it('exists in content', () => {
      render(
        <Select defaultValue="test">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="test">Test Item</SelectItem>
          </SelectContent>
        </Select>
      )

      // When value is selected, the text should appear in trigger
      expect(screen.getByText('Test Item')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has combobox role on trigger', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option">Option</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('has aria-expanded attribute', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option">Option</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByRole('combobox')
      expect(trigger).toHaveAttribute('aria-expanded', 'false')
    })

    it('has autocomplete attribute', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option">Option</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByRole('combobox')
      expect(trigger).toHaveAttribute('aria-autocomplete', 'none')
    })
  })

  describe('Display names', () => {
    it('has correct display names for debugging', () => {
      // This test ensures components export correctly with display names
      expect(SelectTrigger.displayName).toBeDefined()
    })
  })

  describe('SelectGroup and SelectLabel', () => {
    it('renders grouped structure', () => {
      render(
        <Select defaultValue="apple">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Fruits</SelectLabel>
              <SelectItem value="apple">Apple</SelectItem>
              <SelectItem value="banana">Banana</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      )

      // Selected value displays in trigger
      expect(screen.getByText('Apple')).toBeInTheDocument()
    })
  })

  describe('SelectSeparator', () => {
    it('renders as part of content structure', () => {
      render(
        <Select defaultValue="item1">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="item1">Item 1</SelectItem>
            <SelectSeparator data-testid="separator" className="my-separator" />
            <SelectItem value="item2">Item 2</SelectItem>
          </SelectContent>
        </Select>
      )

      // Just verify the select renders correctly with separator in structure
      expect(screen.getByText('Item 1')).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('trigger has rounded corners', () => {
      render(
        <Select>
          <SelectTrigger data-testid="trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="a">A</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByTestId('trigger')).toHaveClass('rounded-md')
    })

    it('trigger has proper padding', () => {
      render(
        <Select>
          <SelectTrigger data-testid="trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="a">A</SelectItem>
          </SelectContent>
        </Select>
      )

      expect(screen.getByTestId('trigger')).toHaveClass('px-3', 'py-2')
    })

    it('trigger has focus ring styles', () => {
      render(
        <Select>
          <SelectTrigger data-testid="trigger">
            <SelectValue placeholder="Select" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="a">A</SelectItem>
          </SelectContent>
        </Select>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger.className).toContain('focus:')
    })
  })
})
