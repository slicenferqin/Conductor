/**
 * API client for Conductor backend.
 */

import type { Project, Message } from '../types';

const API_BASE = 'http://localhost:5566';

interface ApiError {
  detail: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'Unknown error',
      }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  // Project endpoints
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/api/projects');
  }

  async getProject(projectId: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}`);
  }

  async createProject(requirement: string): Promise<Project> {
    return this.request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ requirement }),
    });
  }

  async updateProject(
    projectId: string,
    action: 'pause' | 'resume' | 'stop'
  ): Promise<{ status: string; action: string }> {
    return this.request(`/api/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify({ action }),
    });
  }

  // Message endpoints
  async getMessages(
    projectId: string,
    limit: number = 1000,
    offset: number = 0
  ): Promise<Message[]> {
    return this.request<Message[]>(
      `/api/projects/${projectId}/messages?limit=${limit}&offset=${offset}`
    );
  }

  async sendMessage(
    projectId: string,
    content: string,
    mentions: string[] = []
  ): Promise<Message> {
    return this.request<Message>(`/api/projects/${projectId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, mentions }),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return this.request('/health');
  }

  // File endpoints
  async getProjectFiles(projectId: string): Promise<FileNode[]> {
    try {
        return await this.request<FileNode[]>(`/api/projects/${projectId}/files`);
    } catch (error) {
        console.error('Failed to get project files:', error);
        return [];
    }
  }

  async getFileContent(projectId: string, path: string): Promise<FileContent> {
    const encodedPath = encodeURIComponent(path);
    return this.request<FileContent>(`/api/projects/${projectId}/files/content?path=${encodedPath}`);
  }
}

export const api = new ApiClient();
export default api;

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  last_modified?: number;
  children?: FileNode[];
}

export interface FileContent {
  path: string;
  content: string;
  size: number;
}
