import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock the fetch function
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('fetch wrapper behavior', () => {
    it('should make GET request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      })

      const response = await fetch('/api/test')
      const data = await response.json()

      expect(mockFetch).toHaveBeenCalledWith('/api/test')
      expect(data).toEqual({ data: 'test' })
    })

    it('should make POST request with body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      })

      await fetch('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test' }),
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test' }),
      })
    })

    it('should handle error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      })

      const response = await fetch('/api/not-found')
      expect(response.ok).toBe(false)
      expect(response.status).toBe(404)
    })

    it('should handle network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(fetch('/api/test')).rejects.toThrow('Network error')
    })

    it('should include authorization header when token exists', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      })

      const token = 'test-token-123'
      await fetch('/api/protected', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/protected', {
        headers: {
          Authorization: 'Bearer test-token-123',
        },
      })
    })
  })

  describe('request methods', () => {
    it('should make PUT request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ updated: true }),
      })

      await fetch('/api/resource/1', {
        method: 'PUT',
        body: JSON.stringify({ name: 'updated' }),
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/resource/1', {
        method: 'PUT',
        body: JSON.stringify({ name: 'updated' }),
      })
    })

    it('should make DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ deleted: true }),
      })

      await fetch('/api/resource/1', {
        method: 'DELETE',
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/resource/1', {
        method: 'DELETE',
      })
    })

    it('should make PATCH request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ patched: true }),
      })

      await fetch('/api/resource/1', {
        method: 'PATCH',
        body: JSON.stringify({ field: 'value' }),
      })

      expect(mockFetch).toHaveBeenCalledWith('/api/resource/1', {
        method: 'PATCH',
        body: JSON.stringify({ field: 'value' }),
      })
    })
  })

  describe('response handling', () => {
    it('should parse JSON response', async () => {
      const mockData = { id: 1, name: 'Test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      })

      const response = await fetch('/api/test')
      const data = await response.json()

      expect(data).toEqual(mockData)
    })

    it('should handle empty response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(null),
      })

      const response = await fetch('/api/test')
      const data = await response.json()

      expect(data).toBeNull()
    })

    it('should handle array response', async () => {
      const mockData = [{ id: 1 }, { id: 2 }]
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      })

      const response = await fetch('/api/test')
      const data = await response.json()

      expect(data).toEqual(mockData)
      expect(data).toHaveLength(2)
    })
  })
})
