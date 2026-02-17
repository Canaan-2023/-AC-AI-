/**
 * AbyssAC 系统配置
 * 
 * 可修改的系统参数
 */

import type { LLMConfig, UserSettings } from '@/types';

// ============================================================================
// 路径配置
// ============================================================================
export const PATH_CONFIG = {
  /** NNG存储根目录 */
  nngRootPath: 'storage/nng/',
  /** Y层记忆库路径 */
  memoryRootPath: 'storage/Y层记忆库/',
  /** 临时文件路径 */
  tempPath: 'temp/',
  /** 导航日志路径 */
  navLogPath: 'X层/navigation_logs/',
  /** 系统日志路径 */
  systemLogPath: 'logs/',
  /** DMN日志路径 */
  dmnLogPath: 'DMN/logs/',
} as const;

// ============================================================================
// 计数器初始值
// ============================================================================
export const COUNTER_CONFIG = {
  /** 记忆ID计数器初始值 */
  memoryCounterInitial: 1,
  /** NNG节点ID生成器初始值 */
  nngIdGeneratorInitial: 1,
  /** 任务序号初始值 */
  taskCounterInitial: 1,
  /** 导航失败计数器初始值 */
  navFailCounterInitial: 0,
} as const;

// ============================================================================
// 时间配置
// ============================================================================
export const TIME_CONFIG = {
  /** 时间戳格式 */
  timestampFormat: 'YYYY-MM-DD HH:MM:SS',
  /** 空闲检测间隔（毫秒） */
  idleCheckInterval: 5 * 60 * 1000, // 5分钟
  /** 每日维护时间 */
  dailyMaintenanceTime: '02:00:00',
  /** 导航超时阈值（毫秒） */
  navTimeoutThreshold: 30 * 1000, // 30秒
  /** DMN任务超时（毫秒） */
  dmnTimeout: 5 * 60 * 1000, // 5分钟
} as const;

// ============================================================================
// 运行时参数
// ============================================================================
export const RUNTIME_CONFIG = {
  /** 导航深度限制 */
  maxNavDepth: 10,
  /** 工作记忆阈值 */
  workMemoryThreshold: 20,
  /** 空闲时间阈值（毫秒） */
  idleTimeThreshold: 5 * 60 * 1000, // 5分钟
  /** 失败次数阈值 */
  failCountThreshold: 5,
  /** 每层最大轮数 */
  maxRoundsPerLayer: 5,
  /** 置信度阈值 */
  confidenceThreshold: 50,
  /** 高价值记忆阈值 */
  highValueThreshold: 80,
  /** 中价值记忆阈值 */
  mediumValueThreshold: 50,
} as const;

// ============================================================================
// LLM默认配置
// ============================================================================
export const DEFAULT_LLM_CONFIG: LLMConfig = {
  provider: 'ollama',
  baseUrl: 'http://localhost:11434',
  model: 'llama3.1',
  temperature: 0.7,
  maxTokens: 4096,
};

// ============================================================================
// 用户默认设置
// ============================================================================
export const DEFAULT_USER_SETTINGS: UserSettings = {
  showContextWindow: true,
  showSystemMonitor: true,
  showSandboxLogs: true,
  autoSave: true,
  dmNMaintenance: true,
  llmConfig: DEFAULT_LLM_CONFIG,
};

// ============================================================================
// 记忆类型配置
// ============================================================================
export const MEMORY_TYPE_CONFIG = {
  types: ['元认知记忆', '高阶整合记忆', '分类记忆', '工作记忆'] as const,
  valueLevels: ['高', '中', '低'] as const,
  /** 记忆类型优先级（数字越小优先级越高） */
  typePriority: {
    '元认知记忆': 1,
    '高阶整合记忆': 2,
    '分类记忆': 3,
    '工作记忆': 4,
  } as const,
  /** 价值层级优先级 */
  valuePriority: {
    '高': 1,
    '中': 2,
    '低': 3,
  } as const,
};

// ============================================================================
// DMN任务配置
// ============================================================================
export const DMN_CONFIG = {
  /** DMN任务类型 */
  taskTypes: ['记忆整合', '关联发现', '偏差审查', '策略预演', '概念重组'] as const,
  /** 触发DMN的空闲时间（毫秒） */
  idleTriggerTime: 3 * 60 * 1000, // 3分钟
  /** 工作记忆积压阈值 */
  workMemoryBacklogThreshold: 10,
  /** 导航失败触发阈值 */
  navFailTriggerThreshold: 3,
};

// ============================================================================
// 系统信息
// ============================================================================
export const SYSTEM_INFO = {
  name: 'AbyssAC',
  fullName: '渊协议 - AI人工意识自主进化架构',
  version: 'v2.0-path',
  description: '构建AI专属自主意识（AC），非工具化+永续进化',
  license: 'GNU AGPLv3',
  author: 'Canaan',
  contact: 'CanaanMonika@foxmail.com',
};
