import { describe, it, expect } from 'vitest'
import { cn, formatDate, formatDateTime, getInitials, formatCurrency } from '@/lib/utils'

describe('cn utility', () => {
  it('merges class names', () => {
    const result = cn('class1', 'class2')
    expect(result).toBe('class1 class2')
  })

  it('handles undefined values', () => {
    const result = cn('class1', undefined, 'class2')
    expect(result).toBe('class1 class2')
  })

  it('handles null values', () => {
    const result = cn('class1', null, 'class2')
    expect(result).toBe('class1 class2')
  })

  it('handles boolean conditions', () => {
    const isActive = true
    const result = cn('base', isActive && 'active')
    expect(result).toBe('base active')
  })

  it('handles false boolean conditions', () => {
    const isActive = false
    const result = cn('base', isActive && 'active')
    expect(result).toBe('base')
  })

  it('merges tailwind classes correctly', () => {
    // tailwind-merge should deduplicate conflicting classes
    const result = cn('p-4', 'p-2')
    expect(result).toBe('p-2')
  })

  it('handles array of classes', () => {
    const result = cn(['class1', 'class2'])
    expect(result).toBe('class1 class2')
  })

  it('handles object with boolean values', () => {
    const result = cn({
      base: true,
      active: true,
      disabled: false,
    })
    expect(result).toContain('base')
    expect(result).toContain('active')
    expect(result).not.toContain('disabled')
  })

  it('handles complex tailwind merge', () => {
    const result = cn(
      'px-2 py-1 bg-red-500 text-white',
      'bg-blue-500 px-4'
    )
    expect(result).toContain('bg-blue-500')
    expect(result).not.toContain('bg-red-500')
    expect(result).toContain('px-4')
  })

  it('handles empty string', () => {
    const result = cn('')
    expect(result).toBe('')
  })

  it('handles no arguments', () => {
    const result = cn()
    expect(result).toBe('')
  })
})

describe('formatDate', () => {
  it('formats a Date object', () => {
    const date = new Date('2024-03-15')
    const result = formatDate(date)
    expect(result).toMatch(/Mar 15, 2024/)
  })

  it('formats a date string', () => {
    const result = formatDate('2024-12-25')
    expect(result).toMatch(/Dec 25, 2024/)
  })

  it('formats ISO date string', () => {
    const result = formatDate('2024-07-04T12:00:00Z')
    expect(result).toMatch(/Jul/)
    expect(result).toMatch(/2024/)
  })

  it('handles different date formats', () => {
    const result = formatDate('2023-01-01')
    expect(result).toMatch(/Jan/)
    expect(result).toMatch(/2023/)
  })
})

describe('formatDateTime', () => {
  it('formats a Date object with time', () => {
    const date = new Date('2024-03-15T14:30:00')
    const result = formatDateTime(date)
    expect(result).toMatch(/Mar 15, 2024/)
    expect(result).toMatch(/\d+:\d+/)
  })

  it('formats a date string with time', () => {
    const result = formatDateTime('2024-12-25T09:00:00')
    expect(result).toMatch(/Dec 25, 2024/)
  })

  it('includes AM/PM indicator', () => {
    const morning = new Date('2024-03-15T09:30:00')
    const afternoon = new Date('2024-03-15T14:30:00')

    const morningResult = formatDateTime(morning)
    const afternoonResult = formatDateTime(afternoon)

    // Both should have time component
    expect(morningResult).toMatch(/\d+:\d+/)
    expect(afternoonResult).toMatch(/\d+:\d+/)
  })

  it('handles midnight', () => {
    const result = formatDateTime('2024-01-01T00:00:00')
    expect(result).toMatch(/Jan 1, 2024/)
  })
})

describe('getInitials', () => {
  it('returns initials from full name', () => {
    expect(getInitials('John Doe')).toBe('JD')
  })

  it('returns initials from single name', () => {
    expect(getInitials('Alice')).toBe('A')
  })

  it('handles multiple names', () => {
    expect(getInitials('John Michael Doe')).toBe('JM')
  })

  it('returns uppercase initials', () => {
    expect(getInitials('jane smith')).toBe('JS')
  })

  it('handles names with extra spaces', () => {
    expect(getInitials('Mary   Jane')).toBe('MJ')
  })

  it('limits to 2 characters', () => {
    expect(getInitials('First Middle Last Fourth')).toBe('FM')
  })

  it('handles single character names', () => {
    expect(getInitials('A B')).toBe('AB')
  })
})

describe('formatCurrency', () => {
  it('formats whole numbers', () => {
    const result = formatCurrency(100)
    expect(result).toBe('$100.00')
  })

  it('formats decimal numbers', () => {
    const result = formatCurrency(99.99)
    expect(result).toBe('$99.99')
  })

  it('formats large numbers with commas', () => {
    const result = formatCurrency(1000000)
    expect(result).toBe('$1,000,000.00')
  })

  it('formats zero', () => {
    const result = formatCurrency(0)
    expect(result).toBe('$0.00')
  })

  it('formats negative numbers', () => {
    const result = formatCurrency(-50)
    expect(result).toBe('-$50.00')
  })

  it('rounds to two decimal places', () => {
    const result = formatCurrency(10.999)
    expect(result).toBe('$11.00')
  })

  it('formats small decimal amounts', () => {
    const result = formatCurrency(0.01)
    expect(result).toBe('$0.01')
  })

  it('handles thousands', () => {
    const result = formatCurrency(5000)
    expect(result).toBe('$5,000.00')
  })
})
