import axios, { AxiosInstance } from 'axios';
import type {
  ResearchRequest,
  ResearchTask,
  ResearchStatus,
  ResearchReport
} from './types';

class ResearchAPI {
  private client: AxiosInstance;

  constructor(baseURL?: string) {
    this.client = axios.create({
      baseURL: baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.data?.error) {
          throw new Error(error.response.data.error.message || 'An error occurred');
        }
        throw error;
      }
    );
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