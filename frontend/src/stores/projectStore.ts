import { create } from 'zustand';
import type { Project, TeamMember, Message, AgentStatus } from '../types';

interface ProjectState {
  // Projects list
  projects: Project[];
  currentProjectId: string | null;

  // Current project data
  messages: Message[];

  // Actions
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  setCurrentProject: (projectId: string | null) => void;
  updateProjectStatus: (projectId: string, status: Project['status']) => void;
  updateProjectRequirement: (projectId: string, requirement: string) => void;

  // Team actions
  updateAgentStatus: (
    projectId: string,
    agentId: string,
    status: AgentStatus,
    currentAction?: string,
    progress?: number,
    errorMessage?: string
  ) => void;
  setTeam: (projectId: string, team: TeamMember[]) => void;
  addTeamMember: (projectId: string, member: TeamMember) => void;

  // Message actions
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;

  // Computed
  getCurrentProject: () => Project | undefined;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProjectId: null,
  messages: [],

  setProjects: (projects) => set({ projects }),

  addProject: (project) => set((state) => {
    // Prevent duplicate projects (API + WebSocket may both add)
    const exists = state.projects.some(p => p.id === project.id);
    if (exists) {
      return state;
    }
    return { projects: [project, ...state.projects] };
  }),

  setCurrentProject: (projectId) => {
    // Only clear messages if switching to a DIFFERENT project
    const current = get().currentProjectId;
    if (current !== projectId) {
      set({
        currentProjectId: projectId,
        messages: [], // Clear messages only on switch
      });
    }
  },

  updateProjectStatus: (projectId, status) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, status } : p
    ),
  })),

  updateProjectRequirement: (projectId, requirement) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, requirement } : p
    ),
  })),

  updateAgentStatus: (projectId, agentId, status, currentAction, progress, errorMessage) =>
    set((state) => ({
      projects: state.projects.map((p) =>
        p.id === projectId
          ? {
              ...p,
              team: p.team.map((member) =>
                member.id === agentId
                  ? { ...member, status, currentAction, progress, errorMessage }
                  : member
              ),
            }
          : p
      ),
    })),

  setTeam: (projectId, team) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, team } : p
    ),
  })),

  addTeamMember: (projectId, member) => set((state) => ({
    projects: state.projects.map((p) =>
      p.id === projectId ? { ...p, team: [...p.team, member] } : p
    ),
  })),

  setMessages: (newMessages) => set((state) => {
    // Merge messages: keep existing messages not in newMessages, then add newMessages
    // This prevents WebSocket messages from being overwritten by API responses
    const existingIds = new Set(newMessages.map(m => m.id));
    const uniqueExisting = state.messages.filter(m => !existingIds.has(m.id));
    // Combine: API messages first (historical), then any newer WebSocket messages
    const combined = [...newMessages, ...uniqueExisting];
    // Sort by timestamp to maintain order
    combined.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    return { messages: combined };
  }),

  addMessage: (message) => set((state) => {
    // Prevent duplicate messages
    if (state.messages.some(m => m.id === message.id)) {
      return state;
    }
    return { messages: [...state.messages, message] };
  }),

  getCurrentProject: () => {
    const state = get();
    return state.projects.find((p) => p.id === state.currentProjectId);
  },
}));

// Mock data for development
export const mockProject: Project = {
  id: 'proj-001',
  name: '调研字节跳动这家公司...',
  requirement: '调研一下字节跳动这家公司，出一份较为详尽和专业的调研报告，并且最终做成可视化页面',
  workspace: '/projects/proj-001',
  status: 'RUNNING',
  team: [
    {
      id: 'agent-1',
      role: { id: 'researcher', name: '调研员', emoji: '🔍', description: '负责信息收集、资料整理' },
      status: 'WORKING',
      currentAction: '📖 读取 docs/research.md',
      progress: 65,
    },
    {
      id: 'agent-2',
      role: { id: 'analyst', name: '分析师', emoji: '📊', description: '负责数据分析、趋势研判' },
      status: 'WAITING',
      currentAction: '等待 @调研员 完成',
    },
    {
      id: 'agent-3',
      role: { id: 'writer', name: '撰稿人', emoji: '✍️', description: '负责文档撰写、内容创作' },
      status: 'ONLINE',
    },
    {
      id: 'agent-4',
      role: { id: 'frontend', name: '前端开发', emoji: '🎨', description: '负责前端 UI 开发' },
      status: 'ONLINE',
    },
    {
      id: 'agent-5',
      role: { id: 'reviewer', name: '验收员', emoji: '✅', description: '负责产出物验收、质量检查' },
      status: 'OFFLINE',
    },
  ],
  createdAt: new Date().toISOString(),
};

export const mockMessages: Message[] = [
  {
    id: 'msg-1',
    projectId: 'proj-001',
    fromId: 'user',
    fromName: '👤 用户',
    content: '调研一下字节跳动这家公司，出一份较为详尽和专业的调研报告，并且最终做成可视化页面',
    mentions: [],
    attachments: [],
    timestamp: new Date(Date.now() - 300000).toISOString(),
    type: 'user',
  },
  {
    id: 'msg-2',
    projectId: 'proj-001',
    fromId: 'secretary',
    fromName: '🤖 秘书',
    content: '团队已组建完成！\n\n📋 项目: 调研字节跳动...\n\n👥 团队成员:\n  🔍 调研员\n  📊 分析师\n  ✍️ 撰稿人\n  🎨 前端开发\n  ✅ 验收员',
    mentions: [],
    attachments: [],
    timestamp: new Date(Date.now() - 290000).toISOString(),
    type: 'system',
  },
  {
    id: 'msg-3',
    projectId: 'proj-001',
    fromId: 'agent-1',
    fromName: '🔍 调研员 💭',
    content: '📖 读取文件: requirements.md',
    mentions: [],
    attachments: [],
    timestamp: new Date(Date.now() - 280000).toISOString(),
    type: 'progress',
  },
  {
    id: 'msg-4',
    projectId: 'proj-001',
    fromId: 'agent-1',
    fromName: '🔍 调研员',
    content: '**调研任务已完成！**\n\n我已完成字节跳动公司的详细调研报告，主要发现：\n\n1. **公司规模**：估值达5000亿美元\n2. **核心产品**：抖音、TikTok、今日头条\n\n📎 docs/research.md\n\n@分析师 @前端开发 调研报告已完成，请进行后续工作。',
    mentions: ['分析师', '前端开发'],
    attachments: ['docs/research.md'],
    timestamp: new Date(Date.now() - 120000).toISOString(),
    type: 'agent',
  },
];
