/**
 * AI Corp API Client
 *
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Types
export interface Message {
  id: string;
  role: 'user' | 'coo';
  content: string;
  timestamp: Date;
  context?: {
    type: 'project' | 'agent' | 'gate' | 'system';
    reference: string;
  };
}

export interface ConversationThread {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  unread: boolean;
}

export interface ImageAttachment {
  data: string;  // Base64-encoded image data
  media_type: string;  // MIME type (image/png, image/jpeg, etc.)
}

export interface COOMessageResponse {
  response: string;
  thread_id: string;
  timestamp: string;
  actions_taken?: Array<{ action: string; details: string }>;
}

export interface DashboardMetrics {
  agents_active: number;
  agents_total: number;
  projects_active: number;
  gates_pending: number;
  queue_depth: number;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  progress: number;
  priority: string;
  created_at: string;
  steps_total: number;
  steps_completed: number;
  workers_active?: number;
  current_phase?: string;
}

export interface Gate {
  id: string;
  name: string;
  gate_type: string;
  status: string;
}

export interface PendingGate {
  gate_id: string;
  submission_id: string;
  submitted_by: string;
  submitted_at: string;
  artifacts: string[];
}

export interface ActivityItem {
  id: string;
  action: string;
  agent_id: string;
  message: string;
  timestamp: string;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  projects: Project[];
  gates_pending: PendingGate[];
  activity: ActivityItem[];
  alerts: Array<{ id: string; type: string; message: string }>;
}

// API Client
class APIClient {
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
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // ==========================================================================
  // COO Chat
  // ==========================================================================

  async sendCOOMessage(
    message: string,
    threadId?: string,
    context?: Record<string, unknown>,
    images?: ImageAttachment[]
  ): Promise<COOMessageResponse> {
    return this.request<COOMessageResponse>('/api/coo/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        thread_id: threadId,
        context,
        images: images && images.length > 0 ? images : undefined,
      }),
    });
  }

  async getCOOThreads(): Promise<{ threads: ConversationThread[] }> {
    return this.request('/api/coo/threads');
  }

  async getCOOThread(threadId: string): Promise<ConversationThread & { messages: Message[] }> {
    return this.request(`/api/coo/threads/${threadId}`);
  }

  // ==========================================================================
  // Discovery
  // ==========================================================================

  async startDiscovery(
    initialRequest: string,
    title?: string
  ): Promise<{ session_id: string; response: string; extracted_contract: unknown }> {
    return this.request('/api/discovery/start', {
      method: 'POST',
      body: JSON.stringify({
        initial_request: initialRequest,
        title,
      }),
    });
  }

  async sendDiscoveryMessage(
    sessionId: string,
    message: string
  ): Promise<{ response: string; status: string; extracted_contract: unknown }> {
    return this.request(`/api/discovery/${sessionId}/message`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  async finalizeDiscovery(
    sessionId: string
  ): Promise<{ contract_id: string; molecule_id: string; status: string }> {
    return this.request(`/api/discovery/${sessionId}/finalize`, {
      method: 'POST',
    });
  }

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  async getDashboard(): Promise<DashboardData> {
    return this.request('/api/dashboard');
  }

  async getMetrics(): Promise<DashboardMetrics> {
    return this.request('/api/dashboard/metrics');
  }

  // ==========================================================================
  // Projects
  // ==========================================================================

  async getProjects(status?: string): Promise<{ projects: Project[] }> {
    const query = status ? `?status=${status}` : '';
    return this.request(`/api/projects${query}`);
  }

  async getProject(projectId: string): Promise<Project & { steps: unknown[] }> {
    return this.request(`/api/projects/${projectId}`);
  }

  // ==========================================================================
  // Gates
  // ==========================================================================

  async getGates(): Promise<{ gates: Gate[] }> {
    return this.request('/api/gates');
  }

  async getPendingGates(): Promise<{ pending: PendingGate[] }> {
    return this.request('/api/gates/pending');
  }

  async approveGate(
    gateId: string,
    submissionId: string
  ): Promise<{ status: string; result: unknown }> {
    return this.request(`/api/gates/${gateId}/approve?submission_id=${submissionId}`, {
      method: 'POST',
    });
  }

  async rejectGate(
    gateId: string,
    submissionId: string,
    reason?: string
  ): Promise<{ status: string; result: unknown }> {
    return this.request(
      `/api/gates/${gateId}/reject?submission_id=${submissionId}&reason=${encodeURIComponent(reason || '')}`,
      { method: 'POST' }
    );
  }

  // ==========================================================================
  // Health
  // ==========================================================================

  async healthCheck(): Promise<{ status: string; timestamp: string; version: string }> {
    return this.request('/api/health');
  }
}

// Export singleton instance
export const api = new APIClient();

// Export class for custom instances
export { APIClient };
