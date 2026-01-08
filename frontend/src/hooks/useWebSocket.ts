/**
 * WebSocket hook for real-time updates from Conductor backend.
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import type { Message, TeamMember, Project } from '../types';

const WS_URL = 'ws://localhost:5566/ws';
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

interface WSMessage {
  type: string;
  payload: unknown;
}

interface AgentStatusPayload {
  projectId: string;
  agentId: string;
  status: string;
  currentAction?: string;
  progress?: number;
  errorMessage?: string;
}

interface TeamFormedPayload {
  projectId: string;
  team: TeamMember[];
}

interface ProjectStatusPayload {
  projectId: string;
  status: string;
  error?: string;
}

interface RequirementsUpdatedPayload {
  projectId: string;
  requirements: string;
}

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<number | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const pendingSubscriptions = useRef<Set<string>>(new Set());

  const {
    addProject,
    addMessage,
    updateAgentStatus,
    updateProjectStatus,
    updateProjectRequirement,
    setTeam,
  } = useProjectStore();

  const handleMessage = useCallback(
    (data: WSMessage) => {
      console.log('[WS] Received:', data.type, data.payload);

      switch (data.type) {
        case 'agent_status_changed': {
          const payload = data.payload as AgentStatusPayload;
          updateAgentStatus(
            payload.projectId,
            payload.agentId,
            payload.status as any,
            payload.currentAction,
            payload.progress,
            payload.errorMessage
          );
          break;
        }

        case 'new_message': {
          const message = data.payload as Message;
          addMessage(message);
          break;
        }

        case 'project_created': {
          const project = data.payload as Project;
          addProject(project);
          break;
        }

        case 'team_formed': {
          const payload = data.payload as TeamFormedPayload;
          setTeam(payload.projectId, payload.team);
          break;
        }

        case 'project_status_changed': {
          const payload = data.payload as ProjectStatusPayload;
          updateProjectStatus(payload.projectId, payload.status as any);
          break;
        }

        case 'requirements_updated': {
          const payload = data.payload as RequirementsUpdatedPayload;
          updateProjectRequirement(payload.projectId, payload.requirements);
          break;
        }

        case 'subscribed':
          console.log('[WS] Successfully subscribed to:', (data.payload as any)?.projectId);
          break;

        case 'unsubscribed':
        case 'pong':
          break;

        case 'error':
          console.error('[WS] Server error:', data.payload);
          break;

        default:
          console.warn('[WS] Unknown message type:', data.type);
      }
    },
    [addProject, addMessage, updateAgentStatus, updateProjectStatus, updateProjectRequirement, setTeam]
  );

  const connect = useCallback(() => {
    // Prevent multiple connections
    if (ws.current?.readyState === WebSocket.OPEN || ws.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    // Clear any existing reconnect timer
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }

    try {
      console.log('[WS] Connecting to', WS_URL);
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () => {
        console.log('[WS] Connected successfully');
        setIsConnected(true);
        setConnectionError(null);
        reconnectAttempts.current = 0;

        // Process any pending subscriptions
        pendingSubscriptions.current.forEach((projectId) => {
          console.log('[WS] Processing pending subscription:', projectId);
          ws.current?.send(JSON.stringify({ type: 'subscribe', projectId }));
        });
      };

      ws.current.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data);
          handleMessage(data);
        } catch (e) {
          console.error('[WS] Failed to parse message:', e);
        }
      };

      ws.current.onclose = (event) => {
        console.log('[WS] Disconnected:', event.code, event.reason);
        setIsConnected(false);
        ws.current = null;

        // Only reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts.current++;
          const delay = RECONNECT_DELAY * Math.min(reconnectAttempts.current, 3);
          console.log(`[WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current}/${MAX_RECONNECT_ATTEMPTS})`);
          reconnectTimer.current = window.setTimeout(connect, delay);
        } else if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
          setConnectionError('Failed to connect to server');
        }
      };

      ws.current.onerror = (error) => {
        console.error('[WS] Error:', error);
      };
    } catch (error) {
      console.error('[WS] Failed to create WebSocket:', error);
      setConnectionError('Failed to create WebSocket connection');
    }
  }, [handleMessage]);

  const subscribe = useCallback((projectId: string) => {
    console.log('[WS] Subscribe requested for:', projectId);
    pendingSubscriptions.current.add(projectId);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'subscribe', projectId }));
    } else {
      console.log('[WS] Socket not open, subscription queued');
    }
  }, []);

  const unsubscribe = useCallback((projectId: string) => {
    pendingSubscriptions.current.delete(projectId);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: 'unsubscribe', projectId }));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (ws.current) {
      ws.current.close(1000, 'Client disconnecting');
      ws.current = null;
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionError,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}

export default useWebSocket;
