// Agent status types
export type AgentStatus = 'ONLINE' | 'WORKING' | 'WAITING' | 'OFFLINE' | 'ERROR';

// Project status types
export type ProjectStatus = 'PLANNING' | 'FORMING' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED';

// Agent role definition
export interface AgentRole {
  id: string;
  name: string;
  emoji: string;
  description: string;
}

// Team member (agent instance)
export interface TeamMember {
  id: string;
  role: AgentRole;
  status: AgentStatus;
  currentAction?: string;  // e.g., "📖 读取 file.md"
  progress?: number;       // 0-100
  errorMessage?: string;
}

// Message in project chat
export interface Message {
  id: string;
  projectId: string;
  fromId: string;
  fromName: string;
  content: string;
  mentions: string[];
  attachments: string[];
  timestamp: string;
  type: 'user' | 'agent' | 'progress' | 'system';
}

// Project
export interface Project {
  id: string;
  name: string;
  requirement: string;
  workspace: string;
  status: ProjectStatus;
  team: TeamMember[];
  createdAt: string;
  lastUpdated?: string;
  duration?: number;  // seconds
}

// WebSocket events
export interface WSEvent {
  type: string;
  payload: unknown;
}

export interface AgentStatusEvent {
  type: 'agent_status_changed';
  payload: {
    projectId: string;
    agentId: string;
    status: AgentStatus;
    currentAction?: string;
    progress?: number;
    errorMessage?: string;
  };
}

export interface NewMessageEvent {
  type: 'new_message';
  payload: Message;
}

export interface ProjectCreatedEvent {
  type: 'project_created';
  payload: Project;
}

export interface TeamFormedEvent {
  type: 'team_formed';
  payload: {
    projectId: string;
    team: TeamMember[];
  };
}
