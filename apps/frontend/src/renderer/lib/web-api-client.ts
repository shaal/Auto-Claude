/**
 * Web API client for Auto Claude shared dashboard.
 * Implements a partial ElectronAPI using fetch() for REST and WebSocket for events.
 * Methods not backed by the API are filled in by the browser mock fallback.
 */
import type { ElectronAPI } from '../../shared/types';
import type { IPCResult } from '../../shared/types/common';

const API_BASE = '/api';
const WS_BASE = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;

type EventCallback = (...args: unknown[]) => void;

class WebEventBus {
  private ws: WebSocket | null = null;
  private listeners = new Map<string, Set<EventCallback>>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(`${WS_BASE}/events`);
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const callbacks = this.listeners.get(data.type);
          if (callbacks) {
            callbacks.forEach((cb) => cb(data.taskId, data.data));
          }
        } catch {
          /* ignore parse errors */
        }
      };
      this.ws.onclose = () => {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };
      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      /* ignore connection errors */
    }
  }

  subscribe(eventType: string, callback: EventCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
    this.connect();
    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }
}

const eventBus = new WebEventBus();

async function apiGet<T>(path: string): Promise<IPCResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`);
    const json = await res.json();
    if (!res.ok) return { success: false, error: json.detail || json.error || res.statusText };
    return { success: true, data: json };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

async function apiPost<T>(path: string, body?: unknown): Promise<IPCResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    const json = await res.json();
    if (!res.ok) return { success: false, error: json.detail || json.error || res.statusText };
    return { success: true, data: json };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

function mapSpecStatus(status: string): string {
  if (status.includes('complete')) return 'completed';
  if (status.includes('in_progress')) return 'building';
  if (status.includes('initialized')) return 'ready';
  return 'backlog';
}

/**
 * Creates a partial ElectronAPI backed by real HTTP/WebSocket calls.
 * Methods not implemented here will be filled in from the browser mock.
 */
export function createWebAPI(): Partial<ElectronAPI> {
  return {
    // Project operations
    getProjects: () => apiGet('/projects'),

    addProject: async (projectPath: string) => apiPost('/projects', { path: projectPath }),

    // Task/spec operations
    getTasks: async (_projectId: string) => {
      const result = await apiGet<any[]>('/specs');
      if (!result.success) return result;
      const tasks = (result.data || []).map((spec: any) => ({
        id: spec.folder,
        specId: spec.folder,
        projectId: _projectId,
        title: spec.name.replace(/-/g, ' '),
        description: '',
        status: mapSpecStatus(spec.status),
        subtasks: [],
        logs: [],
        createdAt: new Date(),
        updatedAt: new Date(),
        progress: spec.progress,
        hasWorktree: spec.has_build,
      }));
      return { success: true, data: tasks };
    },

    createTask: async (_projectId: string, title: string, description: string) =>
      apiPost('/specs', { title, description }),

    startTask: (taskId: string) => {
      apiPost(`/specs/${taskId}/start`, {}).catch(() => {});
    },

    stopTask: (taskId: string) => {
      apiPost(`/specs/${taskId}/stop`, {}).catch(() => {});
    },

    // Event listeners via WebSocket
    onTaskProgress: (callback) => eventBus.subscribe('phase_update', callback),
    onTaskError: (callback) => eventBus.subscribe('error', callback),
    onTaskLog: (callback) => eventBus.subscribe('log', callback),
    onTaskStatusChange: (callback) => eventBus.subscribe('status_change', callback),
    onTaskExecutionProgress: (callback) => eventBus.subscribe('execution_progress', callback),

    // Workspace operations
    getWorktreeDiff: (taskId: string) => apiGet(`/workspace/${taskId}/diff`),
    mergeWorktree: (taskId: string, options?: { noCommit?: boolean }) =>
      apiPost(`/workspace/${taskId}/merge`, options),
    mergeWorktreePreview: (taskId: string) => apiGet(`/workspace/${taskId}/merge-preview`),
    discardWorktree: (taskId: string) => apiPost(`/workspace/${taskId}/discard`),

    // Settings
    getTabState: () => apiGet('/settings/tab-state'),
    saveTabState: (tabState) => apiPost('/settings/tab-state', tabState),
  } as Partial<ElectronAPI>;
}
