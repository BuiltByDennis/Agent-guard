import { apiFetch } from '../src/lib/api';

describe('apiFetch', () => {
  beforeEach(() => {
    // Clear mocks and document cookies before each test
    jest.restoreAllMocks();
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
    // Mock global fetch
    global.fetch = jest.fn();
    
    // Mock window location
    delete (window as any).location;
    window.location = { href: '' } as any;
  });

  it('should construct URL correctly and include credentials', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({}),
    });

    await apiFetch('/test-endpoint');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/test-endpoint',
      expect.objectContaining({ credentials: 'include' })
    );
  });

  it('should attach CSRF token for POST requests', async () => {
    document.cookie = 'csrf_token=test-csrf-token';
    
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
    });

    await apiFetch('/post-endpoint', { method: 'POST' });

    // Extract the headers passed to fetch
    const fetchCall = (global.fetch as jest.Mock).mock.calls[0];
    const headers = fetchCall[1].headers as Headers;
    
    expect(headers.get('X-CSRF-Token')).toBe('test-csrf-token');
  });

  it('should retry request if 401 and refresh succeeds', async () => {
    // 1st fetch: 401 Unauthorized
    // 2nd fetch: /v1/auth/refresh -> 200 OK
    // 3rd fetch: retry original -> 200 OK
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValueOnce({ status: 200, ok: true })
      .mockResolvedValueOnce({ status: 200, ok: true });

    await apiFetch('/protected-endpoint');

    expect(global.fetch).toHaveBeenCalledTimes(3);
    expect((global.fetch as jest.Mock).mock.calls[1][0]).toContain('/v1/auth/refresh');
  });

  it('should redirect to /login if refresh fails', async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValueOnce({ status: 401, ok: false }); // refresh fails

    await apiFetch('/protected-endpoint');

    expect(window.location.href).toBe('/login');
  });
});
