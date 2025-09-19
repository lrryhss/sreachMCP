import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  ResearchRequest,
  ResearchTask,
  ResearchStatus,
  ResearchReport
} from './types';

class ResearchAPI {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (reason?: any) => void;
  }> = [];

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.accessToken) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling and token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 errors (unauthorized)
        if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
          if (this.isRefreshing) {
            // If already refreshing, queue this request
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(() => {
              return this.client(originalRequest);
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Attempt to refresh the token
            const newTokens = await this.refreshAccessToken();
            if (newTokens) {
              this.accessToken = newTokens.accessToken;
              this.refreshToken = newTokens.refreshToken;

              // Update the authorization header for the original request
              originalRequest.headers.Authorization = `Bearer ${this.accessToken}`;

              // Process the queue of failed requests
              this.processQueue(null);

              // Retry the original request
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, process queue with error
            this.processQueue(refreshError);

            // Clear tokens and redirect to login
            this.clearTokens();
            if (typeof window !== 'undefined') {
              window.location.href = '/auth/signin';
            }
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // For non-401 errors or if no refresh token, handle normally
        if (error.response?.data) {
          const errorData = error.response.data as any;
          if (errorData.error) {
            throw new Error(errorData.error.message || errorData.detail || 'An error occurred');
          } else if (errorData.detail) {
            throw new Error(errorData.detail);
          }
        }
        throw error;
      }
    );
  }

  // Process the queue of failed requests
  private processQueue(error: any) {
    this.failedQueue.forEach(promise => {
      if (error) {
        promise.reject(error);
      } else {
        promise.resolve();
      }
    });
    this.failedQueue = [];
  }

  // Clear tokens
  private clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
  }

  // Refresh access token
  private async refreshAccessToken(): Promise<{ accessToken: string; refreshToken: string } | null> {
    if (!this.refreshToken) return null;

    try {
      const response = await axios.post(
        `${this.client.defaults.baseURL}/api/auth/refresh`,
        { refresh_token: this.refreshToken },
        { headers: { 'Content-Type': 'application/json' } }
      );

      if (response.data?.access_token && response.data?.refresh_token) {
        // Notify NextAuth session to update
        if (typeof window !== 'undefined') {
          const event = new CustomEvent('token-refreshed', {
            detail: {
              accessToken: response.data.access_token,
              refreshToken: response.data.refresh_token,
            },
          });
          window.dispatchEvent(event);
        }

        return {
          accessToken: response.data.access_token,
          refreshToken: response.data.refresh_token,
        };
      }
      return null;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }

  // Set access token
  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  // Set refresh token
  setRefreshToken(token: string | null) {
    this.refreshToken = token;
  }

  // Set both tokens
  setTokens(accessToken: string | null, refreshToken: string | null) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  // Start a new research task
  async startResearch(request: ResearchRequest): Promise<ResearchTask> {
    const response = await this.client.post('/api/research', request);
    return response.data;
  }

  // Get research status
  async getResearchStatus(taskId: string): Promise<ResearchStatus> {
    const response = await this.client.get(`/api/research/${taskId}/status`);
    return response.data;
  }

  // Get research report
  async getResearchReport(taskId: string, format: 'json' | 'html' = 'json'): Promise<ResearchReport | string> {
    const response = await this.client.get(`/api/research/${taskId}/result`, {
      params: { format },
      headers: format === 'html' ? { 'Accept': 'text/html' } : { 'Accept': 'application/json' },
    });
    return response.data;
  }

  // Cancel a research task
  async cancelResearch(taskId: string): Promise<void> {
    await this.client.delete(`/api/research/${taskId}/cancel`);
  }

  // Get health status
  async getHealth(): Promise<any> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Create SSE connection for live updates
  createEventSource(taskId: string): EventSource {
    const baseURL = this.client.defaults.baseURL;
    return new EventSource(`${baseURL}/api/research/${taskId}/stream`);
  }

  // Preview search results
  async previewSearch(query: string, maxResults: number = 10): Promise<any> {
    const response = await this.client.post('/api/search/preview', {
      query,
      max_results: maxResults,
    });
    return response.data;
  }
}

// Create and export a singleton instance
const api = new ResearchAPI();
export default api;