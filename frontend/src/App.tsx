import { useState, useCallback, useEffect, useRef } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { TeamPanel } from './components/team/TeamPanel';
import { ChatArea } from './components/chat/ChatArea';
import { ProjectHeader } from './components/project/ProjectHeader';
import { Settings, User, Bell, LayoutGrid, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useProjectStore } from './stores/projectStore';
import { FileBrowser } from './components/files/FileBrowser';
import { useWebSocket } from './hooks/useWebSocket';
import { api } from './services/api';
import type { TeamMember, Message, Project } from './types';

// Mock Agent Profiles
const AGENT_PROFILES: Record<string, any> = {
  secretary: { id: 'secretary', name: '秘书', emoji: '🤖', description: '项目协调与需求分析' },
  researcher: { id: 'researcher', name: '调研员', emoji: '🔍', description: '负责信息收集、资料整理' },
  analyst: { id: 'analyst', name: '分析师', emoji: '📊', description: '负责数据分析、趋势研判' },
  writer: { id: 'writer', name: '撰稿人', emoji: '✍️', description: '负责文档撰写、内容创作' },
  frontend: { id: 'frontend', name: '前端开发', emoji: '🎨', description: '负责前端 UI 开发' },
};

function App() {
  const {
    projects,
    currentProjectId,
    messages,
    setProjects,
    setCurrentProject,
    setMessages,
    addProject,
    addMessage,
    updateProjectRequirement,
    updateProjectStatus,
    addTeamMember,
  } = useProjectStore();

  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>();
  const [showTeamPanel, setShowTeamPanel] = useState(true);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectInput, setNewProjectInput] = useState('');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [showFileBrowser, setShowFileBrowser] = useState(false);

  const { isConnected, subscribe, unsubscribe } = useWebSocket();
  const prevProjectId = useRef<string | null>(null);

  // Load projects on mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const projectList = await api.getProjects();
        setProjects(projectList);
        
        // Restore last selected project from localStorage
        const lastProjectId = localStorage.getItem('lastProjectId');
        
        if (projectList.length > 0) {
          if (!currentProjectId) {
            // Priority: lastProjectId -> first project
            const targetId = lastProjectId && projectList.find(p => p.id === lastProjectId) 
              ? lastProjectId 
              : projectList[0].id;
            setCurrentProject(targetId);
          }
        }
        setApiError(null);
      } catch (error) {
        console.error('Failed to load projects:', error);
      }
    };

    loadProjects();
  }, []); // Only run once on mount

  // Persist currentProjectId
  useEffect(() => {
    if (currentProjectId) {
      localStorage.setItem('lastProjectId', currentProjectId);
    }
  }, [currentProjectId]);

  // Subscribe to project updates when project changes
  useEffect(() => {
    // Unsubscribe from previous project if changed
    if (prevProjectId.current && prevProjectId.current !== currentProjectId) {
      unsubscribe(prevProjectId.current);
    }

    if (currentProjectId) {
      subscribe(currentProjectId);

      // Load messages for the project from API
      const loadMessages = async () => {
        try {
          // Add a small delay to ensure backend is ready or to avoid race conditions with project creation
          const msgs = await api.getMessages(currentProjectId);
          setMessages(msgs);
        } catch (error) {
          console.error('Failed to load messages:', error);
        }
      };
      loadMessages();
    }

    prevProjectId.current = currentProjectId;
  }, [currentProjectId, subscribe, unsubscribe, setMessages]);

  const currentProject = projects.find((p) => p.id === currentProjectId);

  const handleNewProject = useCallback(() => {
    setShowNewProjectModal(true);
    setNewProjectInput('');
    setApiError(null);
  }, []);

  const simulateSecretaryFlow = useCallback((projectId: string, requirement: string) => {
    const addMsg = (content: string, type: Message['type'] = 'agent', fromId = 'secretary', fromName = '🤖 秘书') => {
        const msg: Message = {
            id: `msg-${Date.now()}-${Math.random()}`,
            projectId,
            fromId,
            fromName,
            content,
            mentions: [],
            attachments: [],
            timestamp: new Date().toISOString(),
            type,
        };
        addMessage(msg);
    };

    // 1. Secretary Joins
    setTimeout(() => {
        addTeamMember(projectId, { 
            id: 'secretary', 
            role: AGENT_PROFILES.secretary, 
            status: 'WORKING',
            currentAction: '分析需求中...'
        });
        addMsg('收到您的需求，我正在进行分析拆解...', 'agent');
    }, 600);

    // 2. Pin Requirements
    setTimeout(() => {
        updateProjectRequirement(projectId, requirement);
        addMsg('已将需求拆解并置顶到项目公告。正在为您组建最合适的专家团队...', 'system');
    }, 2000);

    // 3. Form Team (Add Agents one by one)
    setTimeout(() => {
        addTeamMember(projectId, { id: 'agent-1', role: AGENT_PROFILES.researcher, status: 'ONLINE' });
        addMsg('🔍 调研员 加入了团队', 'system');
    }, 3500);

    setTimeout(() => {
        addTeamMember(projectId, { id: 'agent-2', role: AGENT_PROFILES.analyst, status: 'ONLINE' });
        addMsg('📊 分析师 加入了团队', 'system');
    }, 4500);

    // 4. Start Working
    setTimeout(() => {
        updateProjectStatus(projectId, 'RUNNING');
        addMsg('团队组建完毕，开始执行任务！', 'system');
    }, 5500);

  }, [addMessage, addTeamMember, updateProjectRequirement, updateProjectStatus]);

  const handleCreateProject = useCallback(async () => {
    if (!newProjectInput.trim() || isCreatingProject) return;

    setIsCreatingProject(true);
    setApiError(null);

    try {
      // 调用后端 API 创建项目（立即返回 placeholder，后台处理）
      const project = await api.createProject(newProjectInput.trim());

      // 添加到本地状态
      addProject(project);
      setCurrentProject(project.id);

      // 关闭弹窗
      setShowNewProjectModal(false);
      setNewProjectInput('');

      // WebSocket 会自动推送后续更新：
      // - team_formed: 团队组建
      // - new_message: 秘书消息
      // - project_status_changed: 状态变化
      // - agent_status_changed: Agent 状态变化

    } catch (error) {
      console.error('Failed to create project:', error);
      setApiError(error instanceof Error ? error.message : '创建项目失败');
    } finally {
      setIsCreatingProject(false);
    }
  }, [newProjectInput, isCreatingProject, addProject, setCurrentProject]);

  const handleSelectProject = useCallback((projectId: string) => {
    setCurrentProject(projectId);
  }, [setCurrentProject]);

  const handleMention = useCallback((member: TeamMember) => {
    setSelectedAgentId(member.id);
  }, []);

  const handleMentionClick = useCallback((mention: string) => {
    const agent = currentProject?.team.find((m) => m.role.name === mention);
    if (agent) {
      setSelectedAgentId(agent.id);
    }
  }, [currentProject]);

  const handleSendMessage = useCallback(async (content: string, mentions: string[]) => {
    if (!currentProject) return;

    // Local update
    const message: Message = {
        id: `msg-${Date.now()}`,
        projectId: currentProject.id,
        fromId: 'user',
        fromName: 'User',
        content,
        mentions,
        attachments: [],
        timestamp: new Date().toISOString(),
        type: 'user',
    };
    addMessage(message);

    // Try API
    try {
      await api.sendMessage(currentProject.id, content, mentions);
    } catch (error) {
      // Ignore error for now in demo mode
    }
  }, [currentProject, addMessage]);

  const handlePauseProject = useCallback(async () => {
    if (!currentProject) return;
    try {
      await api.updateProject(currentProject.id, 'pause');
    } catch (error) {
      console.error('Failed to pause project:', error);
      alert('演示模式：项目已暂停');
      updateProjectStatus(currentProject.id, 'PAUSED');
    }
  }, [currentProject, updateProjectStatus]);

  const handleResumeProject = useCallback(async () => {
    if (!currentProject) return;
    try {
      await api.updateProject(currentProject.id, 'resume');
    } catch (error) {
      alert('演示模式：项目已恢复');
      updateProjectStatus(currentProject.id, 'RUNNING');
    }
  }, [currentProject, updateProjectStatus]);

  const handleStopProject = useCallback(async () => {
    if (!currentProject) return;
    if (!confirm('确定要停止项目吗？停止后无法恢复。')) return;
    try {
      await api.updateProject(currentProject.id, 'stop');
    } catch (error) {
        alert('演示模式：项目已停止');
        updateProjectStatus(currentProject.id, 'FAILED');
    }
  }, [currentProject, updateProjectStatus]);

  return (
    <div className="h-screen w-full bg-background text-text-primary p-3 flex gap-3 overflow-hidden font-sans selection:bg-primary/30">
        {/* Sidebar - Projects List */}
        <Sidebar
          projects={projects}
          currentProjectId={currentProjectId}
          onSelectProject={handleSelectProject}
          onNewProject={handleNewProject}
        />

        {/* Main Content Area */}
        <main className="flex-1 flex flex-col glass-panel rounded-2xl overflow-hidden relative shadow-2xl">
          {currentProject ? (
            <>
              {/* Header */}
              <header className="h-16 flex-shrink-0 flex items-center justify-between px-6 border-b border-white/10 bg-white/5 backdrop-blur-sm z-10 shadow-sm">
                 <div className="flex items-center gap-4">
                     <h2 className="font-semibold text-lg">{currentProject.name}</h2>
                     <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium border border-primary/20">
                        {currentProject.status}
                     </span>
                 </div>

                 <div className="flex items-center gap-2">
                    {/* Connection status */}
                    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs ${isConnected ? 'text-success' : 'text-text-muted'}`}>
                      {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                      <span>{isConnected ? '已连接' : '离线'}</span>
                    </div>
                    <div className="w-px h-4 bg-white/10 mx-1" />
                    <button
                        onClick={() => setShowTeamPanel(!showTeamPanel)}
                        className={`p-2 rounded-lg transition-all ${showTeamPanel ? 'bg-white/10 text-text-primary' : 'text-text-secondary hover:text-text-primary hover:bg-white/5'}`}
                    >
                        <User size={18} />
                    </button>
                    <div className="w-px h-4 bg-white/10 mx-1" />
                    <button className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all">
                        <Bell size={18} />
                    </button>
                    <button className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all">
                        <Settings size={18} />
                    </button>
                 </div>
              </header>

              {/* Inner Content */}
              <div className="flex-1 flex overflow-hidden relative">
                {/* Chat Area */}
                <div className="flex-1 flex flex-col overflow-hidden relative z-0">
                    <div className="flex-shrink-0 z-20">
                        <ProjectHeader
                        project={currentProject}
                        onPause={handlePauseProject}
                        onResume={handleResumeProject}
                        onStop={handleStopProject}
                        onOpenWorkspace={() => setShowFileBrowser(true)}
                        />
                    </div>
                    <div className="flex-1 flex flex-col min-h-0">
                        <ChatArea
                            messages={messages}
                            team={currentProject.team}
                            requirements={currentProject.requirement}
                            onSend={handleSendMessage}
                            onMentionClick={handleMentionClick}
                        />
                    </div>
                </div>

                {/* Team Panel (Right Drawer) */}
                <div
                    className={`
                        w-80 border-l border-white/5 bg-surface/50 backdrop-blur-xl transition-all duration-300 ease-in-out flex flex-col
                        ${showTeamPanel ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0 absolute right-0 h-full z-20 pointer-events-none'}
                    `}
                >
                  <TeamPanel
                    team={currentProject.team}
                    selectedAgentId={selectedAgentId}
                    onMention={handleMention}
                    onSelectAgent={(member) => setSelectedAgentId(member.id)}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-text-muted">
              <div className="w-16 h-16 rounded-2xl bg-surface-highlight flex items-center justify-center mb-6">
                <LayoutGrid size={32} className="text-text-secondary" />
              </div>
              <h2 className="text-xl font-medium text-text-primary mb-2">未选择项目</h2>
              <p className="max-w-md text-center mb-8">请从左侧选择一个项目或创建一个新项目。</p>
              <button
                onClick={handleNewProject}
                className="px-6 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl font-medium transition-colors shadow-lg shadow-primary/20"
              >
                新建项目
              </button>
            </div>
          )}
        </main>

        {/* New Project Modal */}
        {showNewProjectModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-surface border border-white/10 rounded-2xl p-6 w-full max-w-lg shadow-2xl">
              <h3 className="text-lg font-semibold text-text-primary mb-4">新建项目</h3>

              <div className="mb-4">
                <label className="block text-sm text-text-secondary mb-2">项目需求</label>
                <textarea
                  value={newProjectInput}
                  onChange={(e) => setNewProjectInput(e.target.value)}
                  placeholder="描述你的项目需求，AI 团队将自动组建并开始工作..."
                  className="w-full h-32 px-4 py-3 bg-surface-highlight/50 border border-white/10 rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-primary/50 resize-none"
                  disabled={isCreatingProject}
                />
              </div>

              {apiError && (
                <div className="mb-4 p-3 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
                  {apiError}
                </div>
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowNewProjectModal(false)}
                  className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors"
                  disabled={isCreatingProject}
                >
                  取消
                </button>
                <button
                  onClick={handleCreateProject}
                  disabled={!newProjectInput.trim() || isCreatingProject}
                  className="px-6 py-2 bg-primary hover:bg-primary-hover text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isCreatingProject && <Loader2 size={16} className="animate-spin" />}
                  {isCreatingProject ? '创建中...' : '创建项目'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* File Browser Modal */}
        {currentProject && (
            <FileBrowser
                projectId={currentProject.id}
                isOpen={showFileBrowser}
                onClose={() => setShowFileBrowser(false)}
            />
        )}
    </div>
  );
}

export default App;
