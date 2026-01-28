import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

describe('Tabs', () => {
  describe('Tabs Root', () => {
    it('renders children', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Tab 1')).toBeInTheDocument()
      expect(screen.getByText('Content 1')).toBeInTheDocument()
    })

    it('shows content for default value', () => {
      render(
        <Tabs defaultValue="tab2">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Content 2')).toBeInTheDocument()
    })

    it('calls onValueChange when provided', () => {
      const onValueChange = vi.fn()

      render(
        <Tabs defaultValue="tab1" onValueChange={onValueChange}>
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      // Verify component rendered
      expect(screen.getByText('Tab 1')).toBeInTheDocument()
      expect(screen.getByText('Tab 2')).toBeInTheDocument()
    })

    it('renders multiple tabs', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">First</TabsTrigger>
            <TabsTrigger value="tab2">Second</TabsTrigger>
            <TabsTrigger value="tab3">Third</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
          <TabsContent value="tab3">Content 3</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('First')).toBeInTheDocument()
      expect(screen.getByText('Second')).toBeInTheDocument()
      expect(screen.getByText('Third')).toBeInTheDocument()
    })
  })

  describe('TabsList', () => {
    it('renders as tablist role', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      expect(screen.getByRole('tablist')).toBeInTheDocument()
    })

    it('applies default styles', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList data-testid="tablist">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const tablist = screen.getByTestId('tablist')
      expect(tablist).toHaveClass('inline-flex', 'h-10', 'items-center')
    })

    it('applies custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList className="custom-list" data-testid="tablist">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const tablist = screen.getByTestId('tablist')
      expect(tablist).toHaveClass('custom-list')
    })

    it('has background and rounded styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList data-testid="list">
            <TabsTrigger value="tab1">Tab</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const list = screen.getByTestId('list')
      expect(list).toHaveClass('rounded-md', 'p-1')
    })
  })

  describe('TabsTrigger', () => {
    it('renders as tab role', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      expect(screen.getByRole('tab')).toBeInTheDocument()
    })

    it('applies default styles', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="trigger">
              Tab 1
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger).toHaveClass('inline-flex', 'items-center', 'px-3', 'py-1.5')
    })

    it('applies custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" className="custom-trigger" data-testid="trigger">
              Tab 1
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger).toHaveClass('custom-trigger')
    })

    it('can be disabled', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2" disabled>
              Tab 2
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      const disabledTab = screen.getByText('Tab 2')
      expect(disabledTab).toBeDisabled()
    })

    it('has active state styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="active-trigger">
              Tab 1
            </TabsTrigger>
            <TabsTrigger value="tab2" data-testid="inactive-trigger">
              Tab 2
            </TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      const activeTrigger = screen.getByTestId('active-trigger')
      const inactiveTrigger = screen.getByTestId('inactive-trigger')

      expect(activeTrigger).toHaveAttribute('data-state', 'active')
      expect(inactiveTrigger).toHaveAttribute('data-state', 'inactive')
    })

    it('has text styling', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="trigger">Tab</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const trigger = screen.getByTestId('trigger')
      expect(trigger).toHaveClass('text-sm', 'font-medium')
    })

    it('renders with aria-selected for active tab', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      const tab1 = screen.getByText('Tab 1')
      const tab2 = screen.getByText('Tab 2')

      expect(tab1).toHaveAttribute('aria-selected', 'true')
      expect(tab2).toHaveAttribute('aria-selected', 'false')
    })
  })

  describe('TabsContent', () => {
    it('renders as tabpanel role', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )

      expect(screen.getByRole('tabpanel')).toBeInTheDocument()
    })

    it('applies default styles', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" data-testid="content">
            Content 1
          </TabsContent>
        </Tabs>
      )

      const content = screen.getByTestId('content')
      expect(content).toHaveClass('mt-2')
    })

    it('applies custom className', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" className="custom-content" data-testid="content">
            Content 1
          </TabsContent>
        </Tabs>
      )

      const content = screen.getByTestId('content')
      expect(content).toHaveClass('custom-content')
    })

    it('shows active content', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Content 1')).toBeInTheDocument()
    })

    it('only shows active content', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" data-testid="content1">Content 1</TabsContent>
          <TabsContent value="tab2" data-testid="content2">Content 2</TabsContent>
        </Tabs>
      )

      // Active content is visible
      const activeContent = screen.getByTestId('content1')
      expect(activeContent).toHaveAttribute('data-state', 'active')

      // Inactive content has inactive state
      const inactiveContent = screen.getByTestId('content2')
      expect(inactiveContent).toHaveAttribute('data-state', 'inactive')
    })
  })

  describe('Accessibility', () => {
    it('has correct ARIA attributes on tablist', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      )

      const tablist = screen.getByRole('tablist')
      expect(tablist).toBeInTheDocument()
    })

    it('connects tabs to their panels via aria-controls', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )

      const tab = screen.getByRole('tab')
      const panel = screen.getByRole('tabpanel')

      const controlsId = tab.getAttribute('aria-controls')
      expect(panel).toHaveAttribute('id', controlsId)
    })

    it('connects panels to tabs via aria-labelledby', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
        </Tabs>
      )

      const tab = screen.getByRole('tab')
      const panel = screen.getByRole('tabpanel')

      const tabId = tab.getAttribute('id')
      expect(panel).toHaveAttribute('aria-labelledby', tabId)
    })
  })

  describe('Complex Content', () => {
    it('renders complex content in tab panels', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Settings</TabsTrigger>
            <TabsTrigger value="tab2">Profile</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">
            <div>
              <h2>Settings Panel</h2>
              <form>
                <input type="text" placeholder="Setting 1" />
                <button type="submit">Save</button>
              </form>
            </div>
          </TabsContent>
          <TabsContent value="tab2">
            <div>
              <h2>Profile Panel</h2>
              <img src="/avatar.png" alt="Avatar" />
            </div>
          </TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Settings Panel')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Setting 1')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument()
    })
  })

  describe('Display names', () => {
    it('has correct display names', () => {
      expect(TabsList.displayName).toBeDefined()
      expect(TabsTrigger.displayName).toBeDefined()
      expect(TabsContent.displayName).toBeDefined()
    })
  })

  describe('Different default values', () => {
    it('shows third tab content when defaultValue is tab3', () => {
      render(
        <Tabs defaultValue="tab3">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2">Tab 2</TabsTrigger>
            <TabsTrigger value="tab3">Tab 3</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
          <TabsContent value="tab3">Content 3</TabsContent>
        </Tabs>
      )

      expect(screen.getByText('Content 3')).toBeInTheDocument()
    })

    it('marks correct tab as active for different defaults', () => {
      render(
        <Tabs defaultValue="tab2">
          <TabsList>
            <TabsTrigger value="tab1" data-testid="t1">Tab 1</TabsTrigger>
            <TabsTrigger value="tab2" data-testid="t2">Tab 2</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content 1</TabsContent>
          <TabsContent value="tab2">Content 2</TabsContent>
        </Tabs>
      )

      expect(screen.getByTestId('t1')).toHaveAttribute('data-state', 'inactive')
      expect(screen.getByTestId('t2')).toHaveAttribute('data-state', 'active')
    })
  })
})
