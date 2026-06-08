// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { api, setAccessToken } from './api';

describe('API Interceptors - Queue Logic', () => {
  beforeEach(() => {
    setAccessToken(null);
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should intercept 401, refresh token and queue requests', async () => {
    localStorage.setItem('refresh_token', 'valid-refresh-token');
    
    // Simular que axios.post (usado internamente en el interceptor para refresh) resuelve bien
    const axiosPostSpy = vi.spyOn(axios, 'post').mockResolvedValueOnce({
      data: { access_token: 'new-access', refresh_token: 'new-refresh' }
    });

    let callCount = 0;
    // Creamos un custom adapter para simular el fallo 401 inicial y el éxito posterior
    const customAdapter = async (config: any) => {
      callCount++;
      // Las primeras dos peticiones devuelven 401
      if (callCount <= 2) {
        const error: any = new Error('Unauthorized');
        error.config = config;
        error.response = { status: 401 };
        throw error;
      }
      
      // Las peticiones reintentadas devuelven 200 y validan el nuevo token en el header
      return {
        status: 200,
        statusText: 'OK',
        data: `success-for-${config.url}`,
        headers: {},
        config,
        request: {}
      };
    };

    api.defaults.adapter = customAdapter as any;

    // Lanzamos dos peticiones concurrentes
    const req1 = api.get('/protected-1');
    const req2 = api.get('/protected-2');

    const [res1, res2] = await Promise.all([req1, req2]);

    expect(res1.data).toBe('success-for-/protected-1');
    expect(res2.data).toBe('success-for-/protected-2');
    
    // Validamos que axios.post (refresh) se haya llamado solo una vez
    expect(axiosPostSpy).toHaveBeenCalledTimes(1);
    
    // Validamos que se actualizó el storage y se pasaron los headers
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh');
    expect(res1.config.headers['Authorization']).toBe('Bearer new-access');
    expect(res2.config.headers['Authorization']).toBe('Bearer new-access');
  });

  it('should reject queued requests and redirect to login if refresh fails', async () => {
    localStorage.setItem('refresh_token', 'invalid-refresh-token');
    
    // Simular que el refresh falla
    const axiosPostSpy = vi.spyOn(axios, 'post').mockRejectedValueOnce(new Error('Refresh failed'));

    // Mock window.location
    const originalLocation = window.location;
    delete (window as any).location;
    // @ts-ignore
    window.location = { ...originalLocation, href: '' };

    let callCount = 0;
    const customAdapter = async (config: any) => {
      callCount++;
      if (callCount <= 2) {
        const error: any = new Error('Unauthorized');
        error.config = config;
        error.response = { status: 401 };
        throw error;
      }
      return { status: 200, statusText: 'OK', data: 'success', headers: {}, config, request: {} };
    };

    api.defaults.adapter = customAdapter as any;

    const req1 = api.get('/protected-1');
    const req2 = api.get('/protected-2');

    await expect(req1).rejects.toThrow('Refresh failed');
    await expect(req2).rejects.toThrow('Refresh failed');

    expect(axiosPostSpy).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(window.location.href).toBe('/login');

    // Restore window.location
    // @ts-expect-error Restore location
    window.location = originalLocation;
  });
});
