/**
 * AbyssAC 全局状态管理
 * 
 * 使用Zustand管理应用状态
 */

import { create } from 'zustand';
import type {
  ChatMessage,
  SandboxState,
  SandboxLog,
  ContextPackage,
  SystemState,
  SystemMetrics,
  ViewMode,
  UserSettings,
  LLMConfig,
  DMNTask,
} from '@/types';
import { DEFAULT_USER_SETTINGS } from '@/config/system';

// ============================================================================
// 状态定义
// ============================================================================

interface AbyssACState {
  // 视图状态
  currentView: ViewMode;
  setCurrentView: (view: ViewMode) => void;

  // 对话状态
  messages: ChatMessage[];
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;

  // 沙盒状态
  sandboxState: SandboxState | null;
  sandboxLogs: SandboxLog[];
  setSandboxState: (state: SandboxState) => void;
  addSandboxLog: (log: SandboxLog) => void;
  clearSandboxLogs: () => void;

  // 上下文包
  currentContextPackage: ContextPackage | null;
  setCurrentContextPackage: (pkg: ContextPackage | null) => void;

  // 系统状态
  systemState: SystemState;
  updateSystemState: (updates: Partial<SystemState>) => void;

  // 系统监控
  systemMetrics: SystemMetrics;
  updateSystemMetrics: (updates: Partial<SystemMetrics>) => void;

  // DMN任务
  dmnTasks: DMNTask[];
  addDMNTask: (task: DMNTask) => void;
  updateDMNTask: (taskId: string, updates: Partial<DMNTask>) => void;

  // 用户设置
  userSettings: UserSettings;
  updateUserSettings: (updates: Partial<UserSettings>) => void;
  updateLLMConfig: (config: Partial<LLMConfig>) => void;

  // 加载状态
  isProcessing: boolean;
  setIsProcessing: (value: boolean) => void;

  // 错误状态
  error: string | null;
  setError: (error: string | null) => void;

  // 空闲时间追踪
  idleTime: number;
  incrementIdleTime: (delta: number) => void;
  resetIdleTime: () => void;
}

// ============================================================================
// 初始状态
// ============================================================================

const initialSystemState: SystemState = {
  memoryCounter: 1,
  nngIdGenerator: 1,
  taskCounter: 1,
  navFailCounter: 0,
  systemTime: new Date().toISOString(),
  idleTime: 0,
  lastActivityTime: new Date().toISOString(),
  totalMemories: 0,
  totalNNGNodes: 0,
  unprocessedWorkMemories: 0,
  isRunning: true,
  currentTask: null,
};

const initialSystemMetrics: SystemMetrics = {
  memoryDistribution: {
    '元认知记忆': 0,
    '高阶整合记忆': 0,
    '分类记忆': 0,
    '工作记忆': 0,
  },
  valueDistribution: {
    '高': 0,
    '中': 0,
    '低': 0,
  },
  nngDepthDistribution: {},
  avgNavigationTime: 0,
  avgSandboxRounds: 0,
  successRate: 100,
  memoriesByDate: {},
};

// ============================================================================
// Store创建
// ============================================================================

export const useAbyssACStore = create<AbyssACState>((set) => ({
  // 视图状态
  currentView: 'chat',
  setCurrentView: (view) => set({ currentView: view }),

  // 对话状态
  messages: [],
  addMessage: (message) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `msg-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({
      messages: [...state.messages, newMessage],
    }));
  },
  clearMessages: () => set({ messages: [] }),

  // 沙盒状态
  sandboxState: null,
  sandboxLogs: [],
  setSandboxState: (state) => set({ sandboxState: state }),
  addSandboxLog: (log) => {
    set((state) => ({
      sandboxLogs: [...state.sandboxLogs, log],
    }));
  },
  clearSandboxLogs: () => set({ sandboxLogs: [] }),

  // 上下文包
  currentContextPackage: null,
  setCurrentContextPackage: (pkg) => set({ currentContextPackage: pkg }),

  // 系统状态
  systemState: initialSystemState,
  updateSystemState: (updates) => {
    set((state) => ({
      systemState: { ...state.systemState, ...updates },
    }));
  },

  // 系统监控
  systemMetrics: initialSystemMetrics,
  updateSystemMetrics: (updates) => {
    set((state) => ({
      systemMetrics: { ...state.systemMetrics, ...updates },
    }));
  },

  // DMN任务
  dmnTasks: [],
  addDMNTask: (task) => {
    set((state) => ({
      dmnTasks: [...state.dmnTasks, task],
    }));
  },
  updateDMNTask: (taskId, updates) => {
    set((state) => ({
      dmnTasks: state.dmnTasks.map((t) =>
        t.id === taskId ? { ...t, ...updates } : t
      ),
    }));
  },

  // 用户设置
  userSettings: DEFAULT_USER_SETTINGS,
  updateUserSettings: (updates) => {
    set((state) => ({
      userSettings: { ...state.userSettings, ...updates },
    }));
  },
  updateLLMConfig: (config) => {
    set((state) => ({
      userSettings: {
        ...state.userSettings,
        llmConfig: { ...state.userSettings.llmConfig, ...config },
      },
    }));
  },

  // 加载状态
  isProcessing: false,
  setIsProcessing: (value) => set({ isProcessing: value }),

  // 错误状态
  error: null,
  setError: (error) => set({ error }),

  // 空闲时间追踪
  idleTime: 0,
  incrementIdleTime: (delta) => {
    set((state) => ({ idleTime: state.idleTime + delta }));
  },
  resetIdleTime: () => set({ idleTime: 0 }),
}));

// ============================================================================
// 选择器
// ============================================================================

export const selectMessages = (state: AbyssACState) => state.messages;
export const selectCurrentView = (state: AbyssACState) => state.currentView;
export const selectSandboxLogs = (state: AbyssACState) => state.sandboxLogs;
export const selectContextPackage = (state: AbyssACState) => state.currentContextPackage;
export const selectSystemState = (state: AbyssACState) => state.systemState;
export const selectSystemMetrics = (state: AbyssACState) => state.systemMetrics;
export const selectUserSettings = (state: AbyssACState) => state.userSettings;
export const selectIsProcessing = (state: AbyssACState) => state.isProcessing;
export const selectDMNTasks = (state: AbyssACState) => state.dmnTasks;
