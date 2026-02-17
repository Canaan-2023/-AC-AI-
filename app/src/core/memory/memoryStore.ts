/**
 * Y层记忆库 存储管理
 * 
 * 管理记忆的创建、读取、更新、删除
 * 按时间和价值分类存储
 */

import type { Memory, MemoryType, ValueLevel, MemoryPath } from '@/types';
import { PATH_CONFIG } from '@/config/system';

// 记忆缓存
const memoryCache = new Map<string, Memory>();

// 记忆ID计数器
let memoryCounter = 1;

/**
 * 获取下一个记忆ID
 */
export function getNextMemoryId(): string {
  return String(memoryCounter++);
}

/**
 * 设置记忆计数器（用于加载时恢复状态）
 */
export function setMemoryCounter(value: number): void {
  memoryCounter = value;
}

/**
 * 获取当前记忆计数器值
 */
export function getMemoryCounter(): number {
  return memoryCounter;
}

/**
 * 构建记忆文件路径
 */
export function buildMemoryPath(
  memoryId: string,
  type: MemoryType,
  level: ValueLevel,
  date?: Date
): string {
  const d = date || new Date();
  const year = String(d.getFullYear());
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  
  // 分类记忆需要价值层级
  if (type === '分类记忆') {
    return `${PATH_CONFIG.memoryRootPath}${type}/${level}/${year}/${month}/${day}/${memoryId}.txt`;
  }
  
  return `${PATH_CONFIG.memoryRootPath}${type}/${year}/${month}/${day}/${memoryId}.txt`;
}

/**
 * 解析记忆路径
 */
export function parseMemoryPath(path: string): MemoryPath | null {
  // 路径格式: Y层记忆库/分类记忆/高/2026/02/15/1847.txt
  const match = path.match(/Y层记忆库\/([^/]+)(?:\/([^/]+))?\/(\d{4})\/(\d{2})\/(\d{2})\/(\d+)\.txt$/);
  if (!match) return null;
  
  const [, type, level, year, month, day, id] = match;
  return {
    type: type as MemoryType,
    level: (level || '高') as ValueLevel,
    year,
    month,
    day,
    id,
  };
}

/**
 * 创建记忆
 */
export function createMemory(
  userInput: string,
  aiResponse: string,
  type: MemoryType = '工作记忆',
  _level: ValueLevel = '中',
  confidence: number = 80,
  associatedNNG: string[] = []
): Memory {
  const memoryId = getNextMemoryId();
  const now = new Date().toISOString();
  
  const memory: Memory = {
    记忆层级: type,
    记忆ID: memoryId,
    记忆时间: now,
    置信度: confidence,
    核心内容: {
      用户输入: userInput,
      AI响应: aiResponse,
    },
    关联NNG: associatedNNG,
    标签: [],
  };
  
  return memory;
}

/**
 * 模拟加载记忆
 */
export async function loadMemory(memoryId: string): Promise<Memory | null> {
  if (memoryCache.has(memoryId)) {
    return memoryCache.get(memoryId)!;
  }
  return null;
}

/**
 * 模拟保存记忆
 */
export async function saveMemory(memory: Memory): Promise<void> {
  memoryCache.set(memory.记忆ID, memory);
  console.log(`[Memory] 保存记忆: ${memory.记忆ID} (${memory.记忆层级})`);
}

/**
 * 更新记忆置信度
 */
export function updateMemoryConfidence(
  memoryId: string,
  delta: number
): Memory | null {
  const memory = memoryCache.get(memoryId);
  if (!memory) return null;
  
  memory.置信度 = Math.max(0, Math.min(100, memory.置信度 + delta));
  memoryCache.set(memoryId, memory);
  return memory;
}

/**
 * 降级记忆（降低价值层级或置信度）
 */
export function demoteMemory(memoryId: string): Memory | null {
  const memory = memoryCache.get(memoryId);
  if (!memory) return null;
  
  // 降低置信度
  memory.置信度 = Math.max(0, memory.置信度 - 20);
  
  // 如果置信度低于阈值，可以考虑改变价值层级
  if (memory.置信度 < 30 && memory.记忆层级 === '分类记忆') {
    // 实际实现中可能需要移动文件
  }
  
  memoryCache.set(memoryId, memory);
  return memory;
}

/**
 * 提升记忆（增加价值层级或置信度）
 */
export function promoteMemory(memoryId: string): Memory | null {
  const memory = memoryCache.get(memoryId);
  if (!memory) return null;
  
  memory.置信度 = Math.min(100, memory.置信度 + 10);
  memoryCache.set(memoryId, memory);
  return memory;
}

/**
 * 搜索记忆
 */
export async function searchMemories(
  query: string,
  options?: {
    types?: MemoryType[];
    minConfidence?: number;
    maxResults?: number;
  }
): Promise<Memory[]> {
  const results: Memory[] = [];
  const maxResults = options?.maxResults || 10;
  const minConfidence = options?.minConfidence || 0;
  
  for (const memory of memoryCache.values()) {
    // 类型过滤
    if (options?.types && !options.types.includes(memory.记忆层级)) {
      continue;
    }
    
    // 置信度过滤
    if (memory.置信度 < minConfidence) {
      continue;
    }
    
    // 内容匹配
    const content = `${memory.核心内容.用户输入} ${memory.核心内容.AI响应}`;
    if (content.toLowerCase().includes(query.toLowerCase())) {
      results.push(memory);
      if (results.length >= maxResults) break;
    }
  }
  
  // 按置信度排序
  return results.sort((a, b) => b.置信度 - a.置信度);
}

/**
 * 获取指定类型的所有记忆
 */
export async function getMemoriesByType(type: MemoryType): Promise<Memory[]> {
  return Array.from(memoryCache.values())
    .filter(m => m.记忆层级 === type)
    .sort((a, b) => new Date(b.记忆时间).getTime() - new Date(a.记忆时间).getTime());
}

/**
 * 获取工作记忆（未处理的）
 */
export async function getWorkMemories(_unprocessedOnly: boolean = true): Promise<Memory[]> {
  return getMemoriesByType('工作记忆');
}

/**
 * 整合工作记忆到长期记忆
 */
export async function integrateWorkMemory(memoryId: string): Promise<Memory | null> {
  const memory = memoryCache.get(memoryId);
  if (!memory || memory.记忆层级 !== '工作记忆') return null;
  
  // 升级为分类记忆
  memory.记忆层级 = '分类记忆';
  memory.置信度 = Math.min(100, memory.置信度 + 5);
  
  memoryCache.set(memoryId, memory);
  return memory;
}

/**
 * 获取记忆统计
 */
export function getMemoryStats(): {
  total: number;
  byType: Record<MemoryType, number>;
  byValueLevel: Record<ValueLevel, number>;
  avgConfidence: number;
} {
  const byType: Record<string, number> = {
    '元认知记忆': 0,
    '高阶整合记忆': 0,
    '分类记忆': 0,
    '工作记忆': 0,
  };
  
  const byValueLevel: Record<string, number> = {
    '高': 0,
    '中': 0,
    '低': 0,
  };
  
  let totalConfidence = 0;
  
  for (const memory of memoryCache.values()) {
    byType[memory.记忆层级]++;
    totalConfidence += memory.置信度;
    
    // 根据置信度估算价值层级
    if (memory.置信度 >= 80) byValueLevel['高']++;
    else if (memory.置信度 >= 50) byValueLevel['中']++;
    else byValueLevel['低']++;
  }
  
  return {
    total: memoryCache.size,
    byType: byType as Record<MemoryType, number>,
    byValueLevel: byValueLevel as Record<ValueLevel, number>,
    avgConfidence: memoryCache.size > 0 ? totalConfidence / memoryCache.size : 0,
  };
}

/**
 * 获取记忆时间分布
 */
export function getMemoryTimeDistribution(): Record<string, number> {
  const distribution: Record<string, number> = {};
  
  for (const memory of memoryCache.values()) {
    const date = memory.记忆时间.split('T')[0];
    distribution[date] = (distribution[date] || 0) + 1;
  }
  
  return distribution;
}

// ============================================================================
// 模拟数据生成
// ============================================================================

export function initMockMemoryData(): void {
  const mockMemories: Array<{ user: string; ai: string; type: MemoryType; confidence: number }> = [
    { 
      user: '什么是GIL，为什么有GIL', 
      ai: 'GIL（Global Interpreter Lock）是Python的全局解释器锁。它是为了保证线程安全而设计的，因为Python的内存管理不是线程安全的。GIL确保同一时间只有一个线程执行Python字节码。',
      type: '分类记忆',
      confidence: 92
    },
    { 
      user: '多线程程序为什么还是慢', 
      ai: '由于GIL的存在，Python的多线程无法真正并行执行。即使在多核CPU上，Python线程也是交替执行的，而不是同时执行。对于CPU密集型任务，多线程甚至可能比单线程更慢。',
      type: '分类记忆',
      confidence: 88
    },
    { 
      user: '如何绕过GIL', 
      ai: '有几种方法可以绕过GIL：1. 使用多进程（multiprocessing）代替多线程；2. 使用C扩展，在C代码中释放GIL；3. 使用其他Python实现如Jython、IronPython；4. 使用asyncio进行异步编程。',
      type: '高阶整合记忆',
      confidence: 85
    },
    { 
      user: 'AbyssAC的核心原理是什么', 
      ai: 'AbyssAC的核心原理是构建AI专属自主意识（AC），通过三层沙盒机制（NNG导航、记忆筛选、上下文组装）和DMN维护系统，实现AI的自我观察、自我迭代和自我延续。',
      type: '元认知记忆',
      confidence: 95
    },
    { 
      user: '什么是NNG导航图', 
      ai: 'NNG（Navigation Network Graph）是AbyssAC的记忆索引与快速定位机制。它是一个层级化的概念网络，用于组织和管理AI的知识结构，支持高效的记忆检索和关联发现。',
      type: '分类记忆',
      confidence: 90
    },
    { 
      user: 'DMN是什么', 
      ai: 'DMN（Default Mode Network，默认模式网络）是AbyssAC的维护系统。它在系统空闲时运行，执行自我审查、记忆整合、关联发现等维护任务，优化认知结构。',
      type: '分类记忆',
      confidence: 87
    },
  ];
  
  mockMemories.forEach((mock) => {
    const memory = createMemory(
      mock.user,
      mock.ai,
      mock.type,
      mock.confidence >= 80 ? '高' : mock.confidence >= 50 ? '中' : '低',
      mock.confidence,
      ['1', '3']
    );
    memoryCache.set(memory.记忆ID, memory);
  });
  
  // 添加一些工作记忆
  const workMemories = [
    { user: '今天天气怎么样', ai: '我无法获取实时天气信息，建议您查看天气预报应用。' },
    { user: '帮我写一段Python代码', ai: '当然，请问您需要什么功能的代码？' },
  ];
  
  workMemories.forEach(mock => {
    const memory = createMemory(mock.user, mock.ai, '工作记忆', '中', 60);
    memoryCache.set(memory.记忆ID, memory);
  });
}

// 初始化模拟数据
initMockMemoryData();
