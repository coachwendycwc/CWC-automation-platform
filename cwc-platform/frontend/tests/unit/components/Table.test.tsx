import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
} from '@/components/ui/table'

describe('Table', () => {
  describe('Table Root', () => {
    it('renders a table element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      expect(screen.getByRole('table')).toBeInTheDocument()
    })

    it('applies default styles', () => {
      render(
        <Table data-testid="table">
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const table = screen.getByRole('table')
      expect(table).toHaveClass('w-full', 'caption-bottom', 'text-sm')
    })

    it('applies custom className', () => {
      render(
        <Table className="custom-table">
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const table = screen.getByRole('table')
      expect(table).toHaveClass('custom-table')
    })

    it('wraps table in scrollable container', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const table = screen.getByRole('table')
      expect(table.parentElement).toHaveClass('overflow-auto')
    })
  })

  describe('TableHeader', () => {
    it('renders thead element', () => {
      render(
        <Table>
          <TableHeader data-testid="thead">
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const thead = screen.getByTestId('thead')
      expect(thead.tagName).toBe('THEAD')
    })

    it('applies border style to rows', () => {
      render(
        <Table>
          <TableHeader data-testid="thead">
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )

      const thead = screen.getByTestId('thead')
      expect(thead).toHaveClass('[&_tr]:border-b')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableHeader className="custom-header" data-testid="thead">
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )

      const thead = screen.getByTestId('thead')
      expect(thead).toHaveClass('custom-header')
    })
  })

  describe('TableBody', () => {
    it('renders tbody element', () => {
      render(
        <Table>
          <TableBody data-testid="tbody">
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const tbody = screen.getByTestId('tbody')
      expect(tbody.tagName).toBe('TBODY')
    })

    it('removes border from last row', () => {
      render(
        <Table>
          <TableBody data-testid="tbody">
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const tbody = screen.getByTestId('tbody')
      expect(tbody).toHaveClass('[&_tr:last-child]:border-0')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableBody className="custom-body" data-testid="tbody">
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const tbody = screen.getByTestId('tbody')
      expect(tbody).toHaveClass('custom-body')
    })
  })

  describe('TableFooter', () => {
    it('renders tfoot element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
          <TableFooter data-testid="tfoot">
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      )

      const tfoot = screen.getByTestId('tfoot')
      expect(tfoot.tagName).toBe('TFOOT')
    })

    it('applies border and background styles', () => {
      render(
        <Table>
          <TableFooter data-testid="tfoot">
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      )

      const tfoot = screen.getByTestId('tfoot')
      expect(tfoot).toHaveClass('border-t', 'font-medium')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableFooter className="custom-footer" data-testid="tfoot">
            <TableRow>
              <TableCell>Footer</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      )

      const tfoot = screen.getByTestId('tfoot')
      expect(tfoot).toHaveClass('custom-footer')
    })
  })

  describe('TableRow', () => {
    it('renders tr element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow data-testid="row">
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const row = screen.getByTestId('row')
      expect(row.tagName).toBe('TR')
    })

    it('has hover and transition styles', () => {
      render(
        <Table>
          <TableBody>
            <TableRow data-testid="row">
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const row = screen.getByTestId('row')
      expect(row).toHaveClass('border-b', 'transition-colors')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableBody>
            <TableRow className="custom-row" data-testid="row">
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const row = screen.getByTestId('row')
      expect(row).toHaveClass('custom-row')
    })

    it('supports data-state attribute', () => {
      render(
        <Table>
          <TableBody>
            <TableRow data-state="selected" data-testid="row">
              <TableCell>Selected Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const row = screen.getByTestId('row')
      expect(row).toHaveAttribute('data-state', 'selected')
    })
  })

  describe('TableHead', () => {
    it('renders th element', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header Cell</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )

      expect(screen.getByRole('columnheader')).toBeInTheDocument()
    })

    it('applies header styles', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead data-testid="th">Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )

      const th = screen.getByTestId('th')
      expect(th).toHaveClass('h-12', 'px-4', 'text-left', 'font-medium')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="custom-head" data-testid="th">
                Header
              </TableHead>
            </TableRow>
          </TableHeader>
        </Table>
      )

      const th = screen.getByTestId('th')
      expect(th).toHaveClass('custom-head')
    })
  })

  describe('TableCell', () => {
    it('renders td element', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      expect(screen.getByRole('cell')).toBeInTheDocument()
    })

    it('applies cell styles', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell data-testid="td">Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const td = screen.getByTestId('td')
      expect(td).toHaveClass('p-4', 'align-middle')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell className="custom-cell" data-testid="td">
                Cell
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const td = screen.getByTestId('td')
      expect(td).toHaveClass('custom-cell')
    })

    it('supports colSpan attribute', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell colSpan={3} data-testid="td">
                Merged Cell
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const td = screen.getByTestId('td')
      expect(td).toHaveAttribute('colspan', '3')
    })
  })

  describe('TableCaption', () => {
    it('renders caption element', () => {
      render(
        <Table>
          <TableCaption>Table caption text</TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      expect(screen.getByText('Table caption text')).toBeInTheDocument()
    })

    it('applies caption styles', () => {
      render(
        <Table>
          <TableCaption data-testid="caption">Caption</TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const caption = screen.getByTestId('caption')
      expect(caption).toHaveClass('mt-4', 'text-sm')
    })

    it('applies custom className', () => {
      render(
        <Table>
          <TableCaption className="custom-caption" data-testid="caption">
            Caption
          </TableCaption>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      const caption = screen.getByTestId('caption')
      expect(caption).toHaveClass('custom-caption')
    })
  })

  describe('Complete Table', () => {
    it('renders a complete table structure', () => {
      render(
        <Table>
          <TableCaption>A list of users</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>John Doe</TableCell>
              <TableCell>john@example.com</TableCell>
              <TableCell>Active</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Jane Smith</TableCell>
              <TableCell>jane@example.com</TableCell>
              <TableCell>Inactive</TableCell>
            </TableRow>
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell colSpan={2}>Total</TableCell>
              <TableCell>2 users</TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      )

      // Verify structure
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getByText('A list of users')).toBeInTheDocument()
      expect(screen.getAllByRole('columnheader')).toHaveLength(3)
      expect(screen.getAllByRole('row')).toHaveLength(4) // 1 header + 2 body + 1 footer
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('2 users')).toBeInTheDocument()
    })

    it('renders empty table correctly', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column 1</TableHead>
              <TableHead>Column 2</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell colSpan={2}>No data available</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      )

      expect(screen.getByText('No data available')).toBeInTheDocument()
    })
  })
})
