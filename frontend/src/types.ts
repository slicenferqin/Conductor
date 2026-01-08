export type AgentRole = {
  id: string;
  name: string;
  emoji: string;
  description: string;
};

export type AgentStatus = 'ONLINE' | 'WORKING' | 'WAITING' | 'OFFLINE' | 'ERROR';

export type TeamMember = {
  id: string;
  role: AgentRole;
  status: AgentStatus;
  currentAction?: string;
  progress?: number;
  errorMessage?: string;
};

export type Project = {
  id: string;
  name: string;
  status: 'PLANNING' | 'FORMING' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED';
  team: TeamMember[];
  requirement?: string; // Pinned requirements
  workspace?: string;
  createdAt: string;
  lastUpdated?: string;
};

export type MessageType = 'user' | 'agent' | 'system' | 'progress';

export type Message = {
  id: string;
  projectId: string;
  fromId: string;
  fromName: string;
  content: string;
  mentions: string[];
  attachments: string[];
  timestamp: string;
  type: MessageType;
};
