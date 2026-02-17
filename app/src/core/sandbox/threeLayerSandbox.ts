/**
 * 三层沙盒系统
 * 
 * 第一层：NNG导航沙盒 - 定位相关概念节点
 * 第二层：记忆筛选沙盒 - 选择完整记忆
 * 第三层：上下文组装沙盒 - 生成结构化上下文包
 */

import type {
  SandboxState,
  SandboxLog,
  ContextPackage,
  NNGNode,
  Memory,
} from '@/types';
import { loadNNGNode, loadRootNode, parseNNGPath } from '@/core/nng/nngStore';
import { loadMemory, parseMemoryPath } from '@/core/memory/memoryStore';
import { RUNTIME_CONFIG } from '@/config/system';

// ============================================================================
// 沙盒状态管理
// ============================================================================

class ThreeLayerSandbox {
  private state: SandboxState;
  private onLog?: (log: SandboxLog) => void;
  private onStateChange?: (state: SandboxState) => void;

  constructor(
    onLog?: (log: SandboxLog) => void,
    onStateChange?: (state: SandboxState) => void
  ) {
    this.state = this.createInitialState();
    this.onLog = onLog;
    this.onStateChange = onStateChange;
  }

  private createInitialState(): SandboxState {
    return {
      currentLayer: 1,
      round: 1,
      isComplete: false,
      collectedNNG: [],
      collectedMemories: [],
      contextPackage: null,
      logs: [],
    };
  }

  private addLog(log: SandboxLog): void {
    this.state.logs.push(log);
    this.onLog?.(log);
    this.onStateChange?.(this.state);
  }

  private updateState(updates: Partial<SandboxState>): void {
    this.state = { ...this.state, ...updates };
    this.onStateChange?.(this.state);
  }

  // ============================================================================
  // 第一层：NNG导航沙盒
  // ============================================================================

  async runLayer1(userInput: string): Promise<boolean> {
    console.log('[Sandbox] 开始第一层：NNG导航');
    this.addLog({
      layer: 1,
      round: this.state.round,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: '开始NNG导航沙盒',
    });

    let round = 1;
    const collectedNNG: NNGNode[] = [];

    // 第一轮：加载root.json
    const rootNode = await loadRootNode();
    this.addLog({
      layer: 1,
      round,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: '加载根节点',
      paths: ['nng/root.json'],
    });

    // 模拟LLM决策（实际实现中会调用LLM）
    // 这里根据用户输入的关键词选择相关节点
    const selectedPaths = this.simulateLayer1Decision(userInput, rootNode);
    
    while (selectedPaths.length > 0 && round <= RUNTIME_CONFIG.maxRoundsPerLayer) {
      this.addLog({
        layer: 1,
        round,
        timestamp: new Date().toISOString(),
        type: 'output',
        content: `LLM输出路径: ${selectedPaths.join(', ')}`,
        paths: selectedPaths,
      });

      // 并行读取选中的NNG节点
      const nodes = await Promise.all(
        selectedPaths.map(async (path) => {
          const { nodeId } = parseNNGPath(path);
          const node = await loadNNGNode(nodeId);
          return { path, node };
        })
      );

      // 处理读取结果
      for (const { path, node } of nodes) {
        if (node) {
          collectedNNG.push(node);
          this.addLog({
            layer: 1,
            round,
            timestamp: new Date().toISOString(),
            type: 'system',
            content: `成功加载NNG节点: ${node.定位} - ${node.内容.substring(0, 50)}...`,
            paths: [path],
          });
        } else {
          this.addLog({
            layer: 1,
            round,
            timestamp: new Date().toISOString(),
            type: 'error',
            content: `路径不存在: ${path}`,
            paths: [path],
          });
        }
      }

      round++;
      
      // 模拟下一轮决策
      if (round <= RUNTIME_CONFIG.maxRoundsPerLayer) {
        const morePaths = this.simulateLayer1Decision(userInput, rootNode, collectedNNG);
        if (morePaths.length === 0) break;
      }
    }

    this.updateState({
      collectedNNG,
      round,
    });

    this.addLog({
      layer: 1,
      round,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: `第一层完成，共收集 ${collectedNNG.length} 个NNG节点`,
    });

    return true;
  }

  /**
   * 模拟第一层决策（实际实现中会调用LLM）
   */
  private simulateLayer1Decision(
    userInput: string,
    _rootNode: { 一级节点: string[] },
    collectedNNG?: NNGNode[]
  ): string[] {
    const input = userInput.toLowerCase();
    const paths: string[] = [];

    // 根据关键词选择节点
    if (input.includes('系统') || input.includes('架构') || input.includes('核心')) {
      paths.push('nng/1.json');
    }
    if (input.includes('交互') || input.includes('界面') || input.includes('用户')) {
      paths.push('nng/2.json');
    }
    if (input.includes('记忆') || input.includes('存储') || input.includes('NNG')) {
      paths.push('nng/3.json');
    }
    if (input.includes('认知') || input.includes('推理') || input.includes('思考')) {
      paths.push('nng/4.json');
    }
    if (input.includes('意识') || input.includes('自我') || input.includes('元认知')) {
      paths.push('nng/5.json');
    }

    // 如果没有匹配到，默认选择系统核心
    if (paths.length === 0 && !collectedNNG?.length) {
      paths.push('nng/1.json');
    }

    // 如果已经收集了一些节点，探索子节点
    if (collectedNNG?.length && paths.length === 0) {
      for (const node of collectedNNG) {
        if (node.下级关联NNG.length > 0) {
          for (const child of node.下级关联NNG.slice(0, 2)) {
            paths.push(child.路径);
          }
        }
      }
    }

    return paths;
  }

  // ============================================================================
  // 第二层：记忆筛选沙盒
  // ============================================================================

  async runLayer2(userInput: string): Promise<boolean> {
    console.log('[Sandbox] 开始第二层：记忆筛选');
    this.updateState({ currentLayer: 2, round: 1 });
    
    this.addLog({
      layer: 2,
      round: 1,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: '开始记忆筛选沙盒',
    });

    let round = 1;
    const collectedMemories: Memory[] = [];
    const { collectedNNG } = this.state;

    // 从NNG节点中提取记忆摘要
    const memorySummaries = collectedNNG.flatMap(n => n.关联的记忆文件摘要);
    
    this.addLog({
      layer: 2,
      round,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: `从NNG节点中发现 ${memorySummaries.length} 个记忆摘要`,
    });

    // 模拟LLM选择记忆
    let selectedPaths = this.simulateLayer2Decision(userInput, collectedNNG);

    while (selectedPaths.length > 0 && round <= RUNTIME_CONFIG.maxRoundsPerLayer) {
      this.addLog({
        layer: 2,
        round,
        timestamp: new Date().toISOString(),
        type: 'output',
        content: `LLM选择记忆路径: ${selectedPaths.join(', ')}`,
        paths: selectedPaths,
      });

      // 并行读取记忆
      const memories = await Promise.all(
        selectedPaths.map(async (path) => {
          const parsed = parseMemoryPath(path);
          if (parsed) {
            const memory = await loadMemory(parsed.id);
            return { path, memory };
          }
          return { path, memory: null };
        })
      );

      for (const { path, memory } of memories) {
        if (memory) {
          collectedMemories.push(memory);
          this.addLog({
            layer: 2,
            round,
            timestamp: new Date().toISOString(),
            type: 'system',
            content: `成功加载记忆: ${memory.记忆ID} - ${memory.核心内容.用户输入.substring(0, 30)}...`,
            paths: [path],
          });
        } else {
          this.addLog({
            layer: 2,
            round,
            timestamp: new Date().toISOString(),
            type: 'error',
            content: `记忆路径不存在: ${path}`,
            paths: [path],
          });
        }
      }

      round++;

      // 模拟下一轮决策
      if (round <= RUNTIME_CONFIG.maxRoundsPerLayer) {
        selectedPaths = this.simulateLayer2Decision(userInput, collectedNNG, collectedMemories);
        if (selectedPaths.length === 0) break;
      }
    }

    this.updateState({
      collectedMemories,
      round,
    });

    this.addLog({
      layer: 2,
      round,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: `第二层完成，共收集 ${collectedMemories.length} 个记忆`,
    });

    return true;
  }

  /**
   * 模拟第二层决策
   */
  private simulateLayer2Decision(
    userInput: string,
    collectedNNG: NNGNode[],
    _collectedMemories?: Memory[]
  ): string[] {
    const input = userInput.toLowerCase();
    const paths: string[] = [];

    // 从NNG节点的记忆摘要中选择相关记忆
    for (const nng of collectedNNG) {
      for (const summary of nng.关联的记忆文件摘要) {
        // 根据关键词匹配
        if (input.includes('gil') && summary.摘要.toLowerCase().includes('gil')) {
          paths.push(summary.路径);
        }
        if (input.includes('线程') && summary.摘要.toLowerCase().includes('线程')) {
          paths.push(summary.路径);
        }
        if (input.includes('性能') && summary.摘要.toLowerCase().includes('性能')) {
          paths.push(summary.路径);
        }
      }
    }

    // 去重
    return [...new Set(paths)];
  }

  // ============================================================================
  // 第三层：上下文组装沙盒
  // ============================================================================

  async runLayer3(userInput: string): Promise<ContextPackage | null> {
    console.log('[Sandbox] 开始第三层：上下文组装');
    this.updateState({ currentLayer: 3, round: 1 });
    
    this.addLog({
      layer: 3,
      round: 1,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: '开始上下文组装沙盒',
    });

    const { collectedNNG, collectedMemories } = this.state;

    // 构建认知路径
    const cognitivePath = collectedNNG.map(n => n.内容.split(' - ')[0]);

    // 分类记忆
    const coreGroup = collectedMemories
      .filter(m => m.置信度 >= 80)
      .map(m => ({
        记忆ID: m.记忆ID,
        置信度: m.置信度,
        关键内容摘要: m.核心内容.AI响应.substring(0, 100) + '...',
        作用: '直接回答问题的核心信息',
      }));

    const supportGroup = collectedMemories
      .filter(m => m.置信度 >= 50 && m.置信度 < 80)
      .map(m => ({
        记忆ID: m.记忆ID,
        置信度: m.置信度,
        关键内容摘要: m.核心内容.AI响应.substring(0, 100) + '...',
        作用: '提供背景信息和补充说明',
      }));

    // 构建上下文包
    const contextPackage: ContextPackage = {
      问题解析: {
        核心意图: this.extractCoreIntent(userInput),
        关键概念: this.extractKeyConcepts(userInput, collectedNNG),
        隐含需求: this.extractImplicitNeeds(userInput),
      },
      认知路径: {
        路径: cognitivePath,
        路径说明: `通过NNG导航定位到${collectedNNG.length}个相关概念节点`,
      },
      记忆整合: {
        核心组: coreGroup,
        支撑组: supportGroup,
        对比组: [],
      },
      缺失信息: {
        已知但未获取: [],
        疑似存在: [],
        需要澄清: [],
      },
      置信度评估: {
        整体置信度: collectedMemories.length > 0 ? '高' : '中',
        依据: `收集了${collectedMemories.length}个相关记忆，平均置信度${
          collectedMemories.length > 0
            ? Math.round(collectedMemories.reduce((a, b) => a + b.置信度, 0) / collectedMemories.length)
            : 0
        }`,
        风险提示: collectedMemories.length === 0 ? ['未找到相关记忆'] : [],
      },
      回复策略建议: {
        推荐角度: '基于已有记忆进行回答',
        重点强调: collectedMemories.map(m => m.核心内容.用户输入),
        谨慎处理: collectedMemories.length === 0 ? ['信息可能不完整'] : [],
        可扩展方向: ['深入探讨具体实现细节', '询问用户的具体应用场景'],
      },
    };

    this.updateState({
      contextPackage,
      isComplete: true,
    });

    this.addLog({
      layer: 3,
      round: 1,
      timestamp: new Date().toISOString(),
      type: 'system',
      content: '第三层完成，上下文包已生成',
    });

    return contextPackage;
  }

  private extractCoreIntent(userInput: string): string {
    // 简单提取核心意图
    if (userInput.includes('是什么')) return '获取概念定义';
    if (userInput.includes('为什么')) return '理解原因和原理';
    if (userInput.includes('怎么') || userInput.includes('如何')) return '学习方法或步骤';
    if (userInput.includes('比较') || userInput.includes('区别')) return '对比分析';
    return '获取相关信息';
  }

  private extractKeyConcepts(userInput: string, nngNodes: NNGNode[]): string[] {
    const concepts: string[] = [];
    
    // 从用户输入提取
    if (userInput.includes('GIL')) concepts.push('GIL');
    if (userInput.includes('Python')) concepts.push('Python');
    if (userInput.includes('线程')) concepts.push('多线程');
    if (userInput.includes('性能')) concepts.push('性能优化');
    
    // 从NNG节点提取
    nngNodes.forEach(n => {
      const concept = n.内容.split(' - ')[0];
      if (!concepts.includes(concept)) {
        concepts.push(concept);
      }
    });
    
    return concepts;
  }

  private extractImplicitNeeds(userInput: string): string[] {
    const needs: string[] = [];
    
    if (userInput.includes('GIL') && userInput.includes('慢')) {
      needs.push('了解性能瓶颈原因');
      needs.push('寻找优化方案');
    }
    
    if (userInput.includes('是什么')) {
      needs.push('需要基础概念解释');
    }
    
    return needs;
  }

  // ============================================================================
  // 主流程
  // ============================================================================

  async run(userInput: string): Promise<ContextPackage | null> {
    console.log('[Sandbox] 启动三层沙盒，用户输入:', userInput);
    
    // 重置状态
    this.state = this.createInitialState();
    
    // 第一层：NNG导航
    const layer1Success = await this.runLayer1(userInput);
    if (!layer1Success) {
      console.error('[Sandbox] 第一层失败');
      return null;
    }

    // 第二层：记忆筛选
    const layer2Success = await this.runLayer2(userInput);
    if (!layer2Success) {
      console.error('[Sandbox] 第二层失败');
      return null;
    }

    // 第三层：上下文组装
    const contextPackage = await this.runLayer3(userInput);
    
    console.log('[Sandbox] 三层沙盒完成');
    return contextPackage;
  }

  getState(): SandboxState {
    return this.state;
  }

  getLogs(): SandboxLog[] {
    return this.state.logs;
  }
}

// 导出单例
export const sandbox = new ThreeLayerSandbox();

// 导出创建新实例的函数
export function createSandbox(
  onLog?: (log: SandboxLog) => void,
  onStateChange?: (state: SandboxState) => void
): ThreeLayerSandbox {
  return new ThreeLayerSandbox(onLog, onStateChange);
}
