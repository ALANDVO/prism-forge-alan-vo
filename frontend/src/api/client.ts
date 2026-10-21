const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Types
export interface Agent {
  id: number;
  name: string;
  description: string | null;
  workspace_path: string;
  system_prompt: string | null;
  model_config: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  workspace_path: string;
  description?: string;
  system_prompt?: string;
  model_config?: string;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  model_config?: string;
  is_active?: boolean;
}

export interface AgentListResponse {
  agents: Agent[];
  total: number;
}

export interface FileListResponse {
  files: Array<{
    name: string;
    path: string;
    is_dir: boolean;
  }>;
}

export interface FileReadResponse {
  path: string;
  content: string;
}

export interface FileWriteRequest {
  path: string;
  content: string;
}

export interface FileWriteResponse {
  path: string;
  size: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
  demo_mode: boolean;
}

// API functions
export const api = {
  health: {
    check: () => request<HealthResponse>('/health'),
    ready: () => request<{ ready: boolean }>('/health/ready'),
  },

  agents: {
    list: (activeOnly = true) =>
      request<AgentListResponse>(`/agents?active_only=${activeOnly}`),

    get: (id: number) => request<Agent>(`/agents/${id}`),

    create: (data: AgentCreate) =>
      request<Agent>('/agents', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    update: (id: number, data: AgentUpdate) =>
      request<Agent>(`/agents/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),

    delete: (id: number) =>
      request<void>(`/agents/${id}`, {
        method: 'DELETE',
      }),

    files: {
      list: (agentId: number, path = '') =>
        request<FileListResponse>(`/agents/${agentId}/files?path=${encodeURIComponent(path)}`),

      read: (agentId: number, path: string) =>
        request<FileReadResponse>(`/agents/${agentId}/files/read?path=${encodeURIComponent(path)}`),

      write: (agentId: number, data: FileWriteRequest) =>
        request<FileWriteResponse>(`/agents/${agentId}/files/write`, {
          method: 'POST',
          body: JSON.stringify(data),
        }),
    },
  },
};