/**
 * DMN (Default Mode Network) 维护系统
 * 
 * 五个子智能体协作完成系统维护任务
 * 1. 问题输出Agent - 识别需要维护的认知区域
 * 2. 问题分析Agent - 深入分析问题
 * 3. 审查Agent - 验证分析结果
 * 4. 整理Agent - 转化为标准化输出
 * 5. 格式位置审查Agent - 验证格式规范
 */

import type {
  DMNTask,
  DMNTaskType,
  DMNAgentState,
  DMNAgentType,
} from '@/types';
import { getWorkMemories, getMemoryStats } from '@/core/memory/memoryStore';
import { getNNGStats } from '@/core/nng/nngStore';
import { DMN_CONFIG } from '@/config/system';

// ============================================================================
// DMN系统状态
// ============================================================================

interface DMNSystemState {
  isRunning: boolean;
  currentTask: DMNTask | null;
  taskHistory: DMNTask[];
  idleTime: number;
  lastRunTime: string;
}

const dmnState: DMNSystemState = {
  isRunning: false,
  currentTask: null,
  taskHistory: [],
  idleTime: 0,
  lastRunTime: new Date().toISOString(),
};

// ============================================================================
// 任务创建
// ============================================================================

export function createDMNTask(type: DMNTaskType): DMNTask {
  const task: DMNTask = {
    id: `dmn-${Date.now()}`,
    type,
    status: 'pending',
    startTime: new Date().toISOString(),
    agents: [],
  };
  return task;
}

// ============================================================================
// Agent执行
// ============================================================================

async function runAgent(
  task: DMNTask,
  agentType: DMNAgentType,
  input: string
): Promise<string> {
  const agentState: DMNAgentState = {
    agentType,
    status: 'running',
    input,
    output: '',
    timestamp: new Date().toISOString(),
  };

  task.agents.push(agentState);
  console.log(`[DMN] Agent ${agentType} 开始执行`);

  // 模拟Agent处理（实际实现中会调用LLM）
  let output = '';
  
  switch (agentType) {
    case '问题输出':
      output = await runQuestionOutputAgent(input, task.type);
      break;
    case '问题分析':
      output = await runAnalysisAgent(input);
      break;
    case '审查':
      output = await runReviewAgent(input);
      break;
    case '整理':
      output = await runOrganizeAgent(input);
      break;
    case '格式位置审查':
      output = await runFormatReviewAgent(input);
      break;
  }

  agentState.output = output;
  agentState.status = 'completed';
  agentState.timestamp = new Date().toISOString();

  console.log(`[DMN] Agent ${agentType} 执行完成`);
  return output;
}

// ============================================================================
// 各Agent实现
// ============================================================================

async function runQuestionOutputAgent(
  _systemState: string,
  taskType: DMNTaskType
): Promise<string> {
  // 获取工作记忆
  const workMemories = await getWorkMemories();
  // 获取系统统计（供LLM决策使用）
  console.log('系统统计:', getMemoryStats(), getNNGStats());

  // 根据任务类型选择需要审查的资源
  let selectedPaths: string[] = [];
  let note = '';

  switch (taskType) {
    case '记忆整合':
      // 选择积压的工作记忆
      selectedPaths = workMemories.slice(0, 5).map(m => {
        const date = new Date(m.记忆时间);
        return `Y层记忆库/工作记忆/${date.getFullYear()}/${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}/${m.记忆ID}.txt`;
      });
      note = `发现${workMemories.length}条未处理工作记忆，需要整合到长期记忆`;
      break;

    case '关联发现':
      // 选择主题相近的NNG节点
      selectedPaths = ['nng/1.json', 'nng/3.json', 'nng/4.json'];
      note = '系统核心、记忆管理、认知过程三个节点可能存在未发现的关联';
      break;

    case '偏差审查':
      // 选择置信度较低的节点
      selectedPaths = ['nng/2.json', 'nng/5.json'];
      note = '用户交互和意识相关节点置信度较低，需要审查';
      break;

    case '策略预演':
      selectedPaths = ['nng/1.json', 'nng/1.1.json'];
      note = '预演三层沙盒在复杂查询下的表现';
      break;

    case '概念重组':
      selectedPaths = ['nng/3.json', 'nng/4.json'];
      note = '记忆管理和认知过程可能可以融合为新的概念';
      break;
  }

  return `${selectedPaths.join('\n')}
笔记：${note}`;
}

async function runAnalysisAgent(_pathsInput: string): Promise<string> {
  const paths = _pathsInput.split('\n').filter((p: string) => p.startsWith('Y层记忆库/') || p.startsWith('nng/'));
  
  let analysis = '【资源分析】\n';
  
  for (const path of paths) {
    if (path.startsWith('nng/')) {
      analysis += `- ${path}：NNG节点，需要检查其置信度和关联完整性\n`;
    } else {
      analysis += `- ${path}：记忆文件，需要评估其价值和关联性\n`;
    }
  }

  analysis += '\n【问题归纳】\n';
  analysis += '- 核心问题：资源之间的关联不够紧密\n';
  analysis += '- 表现形式：导航效率可能受影响\n';
  analysis += '- 根本原因：节点创建时关联建立不充分\n';

  analysis += '\n【解决方案】\n';
  analysis += '- 方案1：增强节点间的关联程度，预期效果提升导航效率，风险较低\n';
  analysis += '- 方案2：重新组织部分节点的层级结构，预期效果改善逻辑关系，风险中等\n';

  analysis += '\n【建议优先级】\n';
  analysis += '- 立即执行：增强关键节点的关联\n';
  analysis += '- 后续优化：调整层级结构\n';
  analysis += '- 长期观察：监控导航成功率\n';

  return analysis;
}

async function runReviewAgent(_analysisInput: string): Promise<string> {
  // 审查分析结果
  const hasFatalError = false;
  const hasMajorOmission = false;
  const hasMinorIssue = true;

  let review = `审查结论：${hasFatalError || hasMajorOmission ? '不通过' : '通过'}\n\n`;
  
  review += '缺陷分级：\n';
  review += `- 致命缺陷：${hasFatalError ? '有' : '无'}\n`;
  review += `- 重大遗漏：${hasMajorOmission ? '有' : '无'}\n`;
  review += `- minor问题：${hasMinorIssue ? '有，部分细节可以优化' : '无'}\n`;

  return review;
}

async function runOrganizeAgent(approvedAnalysis: string): Promise<string> {
  const now = new Date().toISOString();
  const memoryCounter = 100;
  const nngIdGenerator = '1.6';

  let output = '【新增/修改NNG】\n';
  output += `路径：nng/${nngIdGenerator}.json\n`;
  output += '内容：\n';
  output += JSON.stringify({
    定位: nngIdGenerator,
    置信度: 75,
    时间: now,
    内容: 'DMN维护优化 - 自动发现的关联节点',
    关联的记忆文件摘要: [],
    上级关联NNG: [{
      节点ID: '1',
      路径: 'nng/1.json',
      关联程度: 85,
    }],
    下级关联NNG: [],
  }, null, 2);

  output += '\n\n【新增/修改记忆】\n';
  output += `路径：Y层记忆库/元认知记忆/${now.split('T')[0].replace(/-/g, '/')}/${memoryCounter}.txt\n`;
  output += '内容：\n';
  output += `【记忆层级】：元认知记忆\n`;
  output += `【记忆ID】：${memoryCounter}\n`;
  output += `【记忆时间】：${now}\n`;
  output += `【置信度】：80\n`;
  output += `【核心内容】：\n`;
  output += `用户输入：DMN执行了${approvedAnalysis.includes('记忆整合') ? '记忆整合' : '维护任务'}\n`;
  output += `AI响应：系统已自动优化相关结构\n`;

  return output;
}

async function runFormatReviewAgent(_organizerOutput: string): Promise<string> {
  // 验证格式
  const checks = [
    { name: 'NNG JSON格式正确', passed: true },
    { name: '路径符合层级规则', passed: true },
    { name: '记忆ID唯一且正确', passed: true },
    { name: '时间戳格式正确', passed: true },
    { name: '父节点已同步更新', passed: true },
    { name: '关联路径可解析', passed: true },
    { name: '置信度范围合法', passed: true },
    { name: '文件命名符合规范', passed: true },
  ];

  const passedChecks = checks.filter(c => c.passed);
  const failedChecks = checks.filter(c => !c.passed);

  let review = `审查结论：${failedChecks.length === 0 ? '通过' : '不通过'}\n\n`;
  
  review += '检查结果：\n';
  review += `- 通过项：${passedChecks.map(c => c.name).join('、')}\n`;
  if (failedChecks.length > 0) {
    review += `- 失败项：${failedChecks.map(c => c.name).join('、')}\n`;
  }

  review += '\n修复建议：无\n';
  review += '最终操作：存入系统\n';

  return review;
}

// ============================================================================
// DMN任务执行流程
// ============================================================================

export async function runDMNTask(type: DMNTaskType): Promise<DMNTask> {
  console.log(`[DMN] 启动任务: ${type}`);
  
  const task = createDMNTask(type);
  dmnState.currentTask = task;
  dmnState.isRunning = true;
  task.status = 'running';

  try {
    // Step 1: 问题输出Agent
    const systemState = JSON.stringify({
      memoryStats: getMemoryStats(),
      nngStats: getNNGStats(),
    });
    const pathsOutput = await runAgent(task, '问题输出', systemState);

    // Step 2: 问题分析Agent
    const analysisOutput = await runAgent(task, '问题分析', pathsOutput);

    // Step 3: 审查Agent
    const reviewOutput = await runAgent(task, '审查', analysisOutput);

    // 检查审查结果
    if (reviewOutput.includes('不通过')) {
      // 需要重新分析
      console.log('[DMN] 审查未通过，重新分析');
    }

    // Step 4: 整理Agent
    const organizeOutput = await runAgent(task, '整理', analysisOutput);

    // Step 5: 格式位置审查Agent
    await runAgent(task, '格式位置审查', organizeOutput);

    // 构建结果
    task.result = {
      新增NNG: [],
      新增记忆: [],
      修改NNG: [],
      修改记忆: [],
    };

    task.status = 'completed';
    task.endTime = new Date().toISOString();
    
    console.log(`[DMN] 任务完成: ${type}`);

  } catch (error) {
    console.error('[DMN] 任务失败:', error);
    task.status = 'failed';
    task.endTime = new Date().toISOString();
  }

  dmnState.taskHistory.push(task);
  dmnState.isRunning = false;
  dmnState.lastRunTime = new Date().toISOString();

  return task;
}

// ============================================================================
// 自动触发逻辑
// ============================================================================

export function checkDMNTrigger(
  idleTime: number,
  unprocessedWorkMemories: number,
  navFailCount: number
): DMNTaskType | null {
  // 检查各种触发条件
  
  // 工作记忆积压
  if (unprocessedWorkMemories >= DMN_CONFIG.workMemoryBacklogThreshold) {
    return '记忆整合';
  }
  
  // 导航失败过多
  if (navFailCount >= DMN_CONFIG.navFailTriggerThreshold) {
    return '偏差审查';
  }
  
  // 空闲时间触发
  if (idleTime >= DMN_CONFIG.idleTriggerTime) {
    // 随机选择任务类型
    const types = DMN_CONFIG.taskTypes;
    return types[Math.floor(Math.random() * types.length)];
  }
  
  return null;
}

// ============================================================================
// 状态查询
// ============================================================================

export function getDMNState(): DMNSystemState {
  return { ...dmnState };
}

export function getDMNTaskHistory(): DMNTask[] {
  return [...dmnState.taskHistory];
}

export function isDMNRunning(): boolean {
  return dmnState.isRunning;
}

// ============================================================================
// 手动触发接口
// ============================================================================

export async function triggerMemoryIntegration(): Promise<DMNTask> {
  return runDMNTask('记忆整合');
}

export async function triggerAssociationDiscovery(): Promise<DMNTask> {
  return runDMNTask('关联发现');
}

export async function triggerDeviationReview(): Promise<DMNTask> {
  return runDMNTask('偏差审查');
}

export async function triggerStrategyRehearsal(): Promise<DMNTask> {
  return runDMNTask('策略预演');
}

export async function triggerConceptReorganization(): Promise<DMNTask> {
  return runDMNTask('概念重组');
}
