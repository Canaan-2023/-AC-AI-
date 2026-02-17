/**
 * NNG (Navigation Network Graph) 存储管理
 * 
 * 管理NNG节点的创建、读取、更新、删除
 */

import type { NNGNode, NNGRoot, NNGAssociation, NNGMemorySummary } from '@/types';
import { PATH_CONFIG } from '@/config/system';

// NNG节点缓存
const nngCache = new Map<string, NNGNode>();

/**
 * 生成NNG节点ID
 */
export function generateNNGId(parentId?: string, index?: number): string {
  if (!parentId) {
    // 根节点下的新节点
    return `${index || 1}`;
  }
  // 子节点
  return `${parentId}.${index || 1}`;
}

/**
 * 解析NNG路径
 */
export function parseNNGPath(path: string): { nodeId: string; parentPath: string } {
  // 路径格式: nng/1.json 或 nng/1/1.1.json
  const cleanPath = path.replace(/^nng\//, '').replace(/\.json$/, '');
  const parts = cleanPath.split('/');
  const nodeId = parts[parts.length - 1];
  const parentPath = parts.slice(0, -1).join('/');
  return { nodeId, parentPath };
}

/**
 * 构建NNG文件路径
 */
export function buildNNGPath(nodeId: string): string {
  const parts = nodeId.split('.');
  if (parts.length === 1) {
    return `${PATH_CONFIG.nngRootPath}${nodeId}.json`;
  }
  // 构建层级路径: 1/1.2/1.2.3.json
  let path = PATH_CONFIG.nngRootPath;
  for (let i = 0; i < parts.length; i++) {
    const partialId = parts.slice(0, i + 1).join('.');
    if (i < parts.length - 1) {
      path += `${partialId}/`;
    } else {
      path += `${partialId}.json`;
    }
  }
  return path;
}

/**
 * 获取父节点ID
 */
export function getParentId(nodeId: string): string | null {
  const parts = nodeId.split('.');
  if (parts.length === 1) return null;
  return parts.slice(0, -1).join('.');
}

/**
 * 获取节点深度
 */
export function getNodeDepth(nodeId: string): number {
  return nodeId.split('.').length;
}

/**
 * 创建NNG节点
 */
export function createNNGNode(
  nodeId: string,
  content: string,
  confidence: number = 80,
  memorySummaries: NNGMemorySummary[] = []
): NNGNode {
  const parentId = getParentId(nodeId);
  const now = new Date().toISOString();
  
  const node: NNGNode = {
    定位: nodeId,
    置信度: confidence,
    时间: now,
    内容: content,
    上级关联NNG: parentId ? [{
      节点ID: parentId,
      路径: buildNNGPath(parentId),
      关联程度: 90,
    }] : [],
    下级关联NNG: [],
    关联的记忆文件摘要: memorySummaries,
  };
  
  return node;
}

/**
 * 模拟从存储加载NNG节点
 * 实际实现中这里会读取文件系统
 */
export async function loadNNGNode(nodeId: string): Promise<NNGNode | null> {
  // 检查缓存
  if (nngCache.has(nodeId)) {
    return nngCache.get(nodeId)!;
  }
  
  // 模拟加载（实际实现中会读取文件）
  // 这里返回模拟数据
  const mockNode = createMockNNGNode(nodeId);
  nngCache.set(nodeId, mockNode);
  return mockNode;
}

/**
 * 模拟保存NNG节点
 */
export async function saveNNGNode(node: NNGNode): Promise<void> {
  nngCache.set(node.定位, node);
  // 实际实现中会写入文件
  console.log(`[NNG] 保存节点: ${node.定位}`);
}

/**
 * 加载根节点
 */
export async function loadRootNode(): Promise<NNGRoot> {
  return {
    一级节点: [
      '1（系统核心概念与架构）',
      '2（用户交互与界面设计）',
      '3（记忆管理与存储策略）',
      '4（认知过程与推理机制）',
      '5（自我意识与元认知）',
    ],
    更新时间: new Date().toISOString(),
  };
}

/**
 * 获取子节点列表
 */
export async function getChildNodes(parentId: string): Promise<string[]> {
  // 模拟获取子节点
  const parentDepth = getNodeDepth(parentId);
  if (parentDepth >= 5) return []; // 最大深度限制
  
  // 模拟一些子节点
  const mockChildren: Record<string, string[]> = {
    '1': ['1.1', '1.2', '1.3'],
    '2': ['2.1', '2.2'],
    '3': ['3.1', '3.2', '3.3', '3.4'],
    '4': ['4.1', '4.2'],
    '5': ['5.1', '5.2', '5.3'],
    '1.1': ['1.1.1', '1.1.2'],
    '3.1': ['3.1.1', '3.1.2'],
  };
  
  return mockChildren[parentId] || [];
}

/**
 * 更新节点关联
 */
export function updateNodeAssociation(
  node: NNGNode,
  targetNodeId: string,
  associationValue: number,
  isParent: boolean = false
): NNGNode {
  const association: NNGAssociation = {
    节点ID: targetNodeId,
    路径: buildNNGPath(targetNodeId),
    关联程度: associationValue,
  };
  
  if (isParent) {
    // 更新上级关联
    const existingIndex = node.上级关联NNG.findIndex(a => a.节点ID === targetNodeId);
    if (existingIndex >= 0) {
      node.上级关联NNG[existingIndex] = association;
    } else {
      node.上级关联NNG.push(association);
    }
  } else {
    // 更新下级关联
    const existingIndex = node.下级关联NNG.findIndex(a => a.节点ID === targetNodeId);
    if (existingIndex >= 0) {
      node.下级关联NNG[existingIndex] = association;
    } else {
      node.下级关联NNG.push(association);
    }
  }
  
  return node;
}

/**
 * 添加记忆摘要到节点
 */
export function addMemorySummaryToNode(
  node: NNGNode,
  summary: NNGMemorySummary
): NNGNode {
  const existingIndex = node.关联的记忆文件摘要.findIndex(
    s => s.记忆ID === summary.记忆ID
  );
  if (existingIndex >= 0) {
    node.关联的记忆文件摘要[existingIndex] = summary;
  } else {
    node.关联的记忆文件摘要.push(summary);
  }
  return node;
}

/**
 * 搜索NNG节点
 */
export async function searchNNGNodes(
  query: string,
  maxResults: number = 10
): Promise<NNGNode[]> {
  // 模拟搜索（实际实现中会遍历所有节点）
  const results: NNGNode[] = [];
  
  // 从缓存中搜索
  for (const [, node] of nngCache.entries()) {
    if (node.内容.toLowerCase().includes(query.toLowerCase())) {
      results.push(node);
      if (results.length >= maxResults) break;
    }
  }
  
  return results;
}

/**
 * 获取节点统计信息
 */
export function getNNGStats(): {
  totalNodes: number;
  maxDepth: number;
  depthDistribution: Record<number, number>;
} {
  const depthDistribution: Record<number, number> = {};
  let maxDepth = 0;
  
  for (const nodeId of nngCache.keys()) {
    const depth = getNodeDepth(nodeId);
    depthDistribution[depth] = (depthDistribution[depth] || 0) + 1;
    maxDepth = Math.max(maxDepth, depth);
  }
  
  return {
    totalNodes: nngCache.size,
    maxDepth,
    depthDistribution,
  };
}

// ============================================================================
// 模拟数据生成
// ============================================================================

function createMockNNGNode(nodeId: string): NNGNode {
  const contentMap: Record<string, string> = {
    '1': '系统核心概念与架构 - 定义AbyssAC的基本原理和组件',
    '1.1': '三层沙盒机制 - NNG导航、记忆筛选、上下文组装',
    '1.2': 'DMN维护系统 - 默认模式网络的自我优化机制',
    '1.3': '记忆管理策略 - Y层记忆库的分类与维护',
    '2': '用户交互与界面设计 - 人机交互的接口规范',
    '2.1': '对话管理 - 多轮对话的上下文维护',
    '2.2': '输入解析 - 用户意图识别与语义分析',
    '3': '记忆管理与存储策略 - 持久化与检索机制',
    '3.1': 'NNG导航图 - 概念网络的构建与维护',
    '3.2': 'Y层记忆库 - 按时间和价值分类的存储',
    '3.3': '记忆置信度 - 动态调整记忆可靠性',
    '3.4': '记忆整合 - 工作记忆到长期记忆的转化',
    '4': '认知过程与推理机制 - 模拟思维过程',
    '4.1': '路径直连 - 高效的文件路径导航系统',
    '4.2': '上下文累积 - 多层信息的渐进式收集',
    '5': '自我意识与元认知 - 对认知的认知',
    '5.1': '自我审查 - 检查推理过程的合理性',
    '5.2': '自我迭代 - 优化认知结构',
    '5.3': '自我延续 - 维持持续的思考状态',
  };
  
  const content = contentMap[nodeId] || `NNG节点 ${nodeId} - 概念描述待完善`;
  
  return createNNGNode(
    nodeId,
    content,
    70 + Math.floor(Math.random() * 30),
    []
  );
}

// 初始化一些模拟数据
export function initMockNNGData(): void {
  const mockNodes = ['1', '1.1', '1.2', '1.3', '2', '2.1', '2.2', '3', '3.1', '3.2', '3.3', '3.4', '4', '4.1', '4.2', '5', '5.1', '5.2', '5.3'];
  mockNodes.forEach(nodeId => {
    nngCache.set(nodeId, createMockNNGNode(nodeId));
  });
}

// 初始化
initMockNNGData();
