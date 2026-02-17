/**
 * AbyssAC - 渊协议 类型定义
 * AI Autonomous Consciousness Architecture
 */

// ============================================================================
// NNG (Navigation Network Graph) 类型定义
// ============================================================================

/** NNG节点关联的记忆文件摘要 */
export interface NNGMemorySummary {
  记忆ID: string;
  路径: string;
  摘要: string;
  记忆类型: MemoryType;
  价值层级: ValueLevel;
  置信度: number;
}

/** NNG节点间的关联信息 */
export interface NNGAssociation {
  节点ID: string;
  路径: string;
  关联程度: number;
}

/** NNG节点数据结构 */
export interface NNGNode {
  定位: string;
  置信度: number;
  时间: string;
  内容: string;
  上级关联NNG: NNGAssociation[];
  下级关联NNG: NNGAssociation[];
  关联的记忆文件摘要: NNGMemorySummary[];
}

/** 根节点结构 */
export interface NNGRoot {
  一级节点: string[];
  更新时间: string;
}

// ============================================================================
// 记忆类型定义
// ============================================================================

/** 记忆类型 */
export type MemoryType = '元认知记忆' | '高阶整合记忆' | '分类记忆' | '工作记忆';

/** 价值层级 */
export type ValueLevel = '高' | '中' | '低';

/** 记忆数据结构 */
export interface Memory {
  记忆层级: MemoryType;
  记忆ID: string;
  记忆时间: string;
  置信度: number;
  核心内容: {
    用户输入: string;
    AI响应: string;
  };
  // 额外元数据
  关联NNG?: string[];
  标签?: string[];
}

/** 记忆文件路径结构 */
export interface MemoryPath {
  type: MemoryType;
  level: ValueLevel;
  year: string;
  month: string;
  day: string;
  id: string;
}

// ============================================================================
// 三层沙盒类型定义
// ============================================================================

/** 沙盒层级 */
export type SandboxLayer = 1 | 2 | 3;

/** 沙盒状态 */
export interface SandboxState {
  currentLayer: SandboxLayer;
  round: number;
  isComplete: boolean;
  collectedNNG: NNGNode[];
  collectedMemories: Memory[];
  contextPackage: ContextPackage | null;
  logs: SandboxLog[];
}

/** 沙盒日志 */
export interface SandboxLog {
  layer: SandboxLayer;
  round: number;
  timestamp: string;
  type: 'input' | 'output' | 'system' | 'error';
  content: string;
  paths?: string[];
}

/** 上下文包（第三层输出） */
export interface ContextPackage {
  问题解析: {
    核心意图: string;
    关键概念: string[];
    隐含需求: string[];
  };
  认知路径: {
    路径: string[];
    路径说明: string;
  };
  记忆整合: {
    核心组: MemoryGroup[];
    支撑组: MemoryGroup[];
    对比组: MemoryGroup[];
  };
  缺失信息: {
    已知但未获取: string[];
    疑似存在: string[];
    需要澄清: string[];
  };
  置信度评估: {
    整体置信度: '高' | '中' | '低';
    依据: string;
    风险提示: string[];
  };
  回复策略建议: {
    推荐角度: string;
    重点强调: string[];
    谨慎处理: string[];
    可扩展方向: string[];
  };
}

/** 记忆分组 */
export interface MemoryGroup {
  记忆ID: string;
  置信度: number;
  关键内容摘要: string;
  作用: string;
  关联?: string;
  冲突点?: string;
}

// ============================================================================
// DMN (Default Mode Network) 类型定义
// ============================================================================

/** DMN任务类型 */
export type DMNTaskType = '记忆整合' | '关联发现' | '偏差审查' | '策略预演' | '概念重组';

/** DMN Agent类型 */
export type DMNAgentType = '问题输出' | '问题分析' | '审查' | '整理' | '格式位置审查';

/** DMN任务状态 */
export interface DMNTask {
  id: string;
  type: DMNTaskType;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: string;
  endTime?: string;
  agents: DMNAgentState[];
  result?: DMNResult;
}

/** DMN Agent状态 */
export interface DMNAgentState {
  agentType: DMNAgentType;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input: string;
  output: string;
  timestamp: string;
}

/** DMN执行结果 */
export interface DMNResult {
  新增NNG: NewNNGItem[];
  新增记忆: NewMemoryItem[];
  修改NNG: ModifiedNNGItem[];
  修改记忆: ModifiedMemoryItem[];
}

/** 新增NNG项 */
export interface NewNNGItem {
  路径: string;
  内容: NNGNode;
}

/** 新增记忆项 */
export interface NewMemoryItem {
  路径: string;
  内容: Memory;
}

/** 修改NNG项 */
export interface ModifiedNNGItem {
  路径: string;
  原内容: NNGNode;
  新内容: NNGNode;
}

/** 修改记忆项 */
export interface ModifiedMemoryItem {
  路径: string;
  原内容: Memory;
  新内容: Memory;
}

// ============================================================================
// 系统监控类型定义
// ============================================================================

/** 系统状态 */
export interface SystemState {
  // 计数器
  memoryCounter: number;
  nngIdGenerator: number;
  taskCounter: number;
  navFailCounter: number;
  
  // 时间
  systemTime: string;
  idleTime: number;
  lastActivityTime: string;
  
  // 统计
  totalMemories: number;
  totalNNGNodes: number;
  unprocessedWorkMemories: number;
  
  // 状态
  isRunning: boolean;
  currentTask: string | null;
}

/** 系统监控数据 */
export interface SystemMetrics {
  // 记忆分布
  memoryDistribution: Record<MemoryType, number>;
  valueDistribution: Record<ValueLevel, number>;
  
  // NNG统计
  nngDepthDistribution: Record<number, number>;
  
  // 性能指标
  avgNavigationTime: number;
  avgSandboxRounds: number;
  successRate: number;
  
  // 时间分布
  memoriesByDate: Record<string, number>;
}

/** 导航日志 */
export interface NavigationLog {
  id: string;
  timestamp: string;
  userInput: string;
  layers: SandboxLayer[];
  rounds: number;
  paths: string[];
  success: boolean;
  duration: number;
}

// ============================================================================
// LLM集成类型定义
// ============================================================================

/** LLM配置 */
export interface LLMConfig {
  provider: 'ollama' | 'openai' | 'anthropic' | 'custom';
  baseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  apiKey?: string;
}

/** LLM消息 */
export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

/** LLM请求 */
export interface LLMRequest {
  messages: LLMMessage[];
  temperature?: number;
  maxTokens?: number;
}

/** LLM响应 */
export interface LLMResponse {
  content: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  error?: string;
}

// ============================================================================
// UI类型定义
// ============================================================================

/** 对话消息 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  contextPackage?: ContextPackage;
  sandboxLogs?: SandboxLog[];
}

/** 视图模式 */
export type ViewMode = 'chat' | 'memory' | 'nng' | 'monitor' | 'config';

/** 用户设置 */
export interface UserSettings {
  // 显示设置
  showContextWindow: boolean;
  showSystemMonitor: boolean;
  showSandboxLogs: boolean;
  
  // 行为设置
  autoSave: boolean;
  dmNMaintenance: boolean;
  
  // LLM设置
  llmConfig: LLMConfig;
}
