/**
 * 系统监控面板
 * 
 * 显示AbyssAC系统的各项运行数据和指标
 * 为LLM提供系统状态信息
 */

import { useEffect, useState } from 'react';
import { 
  Activity, 
  Database, 
  Network, 
  Cpu, 
  AlertCircle,
  Layers,
  Brain
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAbyssACStore } from '@/store/abyssacStore';
import { getMemoryStats } from '@/core/memory/memoryStore';
import { getNNGStats } from '@/core/nng/nngStore';
import { getDMNState } from '@/core/dmn/dmnSystem';

export function SystemMonitor() {
  const [memoryStats, setMemoryStats] = useState({
    total: 0,
    byType: { '元认知记忆': 0, '高阶整合记忆': 0, '分类记忆': 0, '工作记忆': 0 },
    byValueLevel: { '高': 0, '中': 0, '低': 0 },
    avgConfidence: 0,
  });
  
  const [nngStats, setNngStats] = useState({
    totalNodes: 0,
    maxDepth: 0,
    depthDistribution: {} as Record<number, number>,
  });

  const [dmnState, setDmnState] = useState({
    isRunning: false,
    taskCount: 0,
  });

  const systemState = useAbyssACStore((state) => state.systemState);
  const idleTime = useAbyssACStore((state) => state.idleTime);

  // 定期刷新统计数据
  useEffect(() => {
    const refreshStats = () => {
      setMemoryStats(getMemoryStats());
      setNngStats(getNNGStats());
      const dmn = getDMNState();
      setDmnState({
        isRunning: dmn.isRunning,
        taskCount: dmn.taskHistory.length,
      });
    };

    refreshStats();
    const interval = setInterval(refreshStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // 格式化空闲时间
  const formatIdleTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}秒`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}分${seconds % 60}秒`;
    const hours = Math.floor(minutes / 60);
    return `${hours}时${minutes % 60}分`;
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-semibold text-slate-100">系统监控</h3>
        </div>
        <Badge 
          variant="outline" 
          className={`text-xs ${
            systemState.isRunning 
              ? 'border-emerald-500/50 text-emerald-400' 
              : 'border-slate-600 text-slate-500'
          }`}
        >
          {systemState.isRunning ? '运行中' : '已停止'}
        </Badge>
      </div>

      {/* 内容区域 */}
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-4">
          {/* 系统概览 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Cpu className="w-3 h-3" />
                系统概览
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">记忆总数</div>
                  <div className="text-lg font-semibold text-slate-200">{memoryStats.total}</div>
                </div>
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">NNG节点</div>
                  <div className="text-lg font-semibold text-slate-200">{nngStats.totalNodes}</div>
                </div>
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">DMN任务</div>
                  <div className="text-lg font-semibold text-slate-200">{dmnState.taskCount}</div>
                </div>
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">空闲时间</div>
                  <div className="text-lg font-semibold text-slate-200">{formatIdleTime(idleTime)}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 记忆分布 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Database className="w-3 h-3" />
                记忆分布
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* 按类型 */}
              <div className="space-y-2">
                <div className="text-xs text-slate-500">按类型</div>
                {Object.entries(memoryStats.byType).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 w-24 truncate">{type}</span>
                    <Progress 
                      value={memoryStats.total > 0 ? (count / memoryStats.total) * 100 : 0} 
                      className="flex-1 h-1.5 bg-slate-700"
                    />
                    <span className="text-xs text-slate-500 w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>

              {/* 按价值层级 */}
              <div className="space-y-2 pt-2 border-t border-slate-700/50">
                <div className="text-xs text-slate-500">按价值层级</div>
                {Object.entries(memoryStats.byValueLevel).map(([level, count]) => (
                  <div key={level} className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 w-8">{level}</span>
                    <Progress 
                      value={memoryStats.total > 0 ? (count / memoryStats.total) * 100 : 0} 
                      className={`flex-1 h-1.5 bg-slate-700 ${
                        level === '高' ? '[&>div]:bg-green-500' :
                        level === '中' ? '[&>div]:bg-yellow-500' :
                        '[&>div]:bg-red-500'
                      }`}
                    />
                    <span className="text-xs text-slate-500 w-8 text-right">{count}</span>
                  </div>
                ))}
              </div>

              {/* 平均置信度 */}
              <div className="pt-2 border-t border-slate-700/50">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">平均置信度</span>
                  <span className={`text-sm font-medium ${
                    memoryStats.avgConfidence >= 70 ? 'text-green-400' :
                    memoryStats.avgConfidence >= 50 ? 'text-yellow-400' :
                    'text-red-400'
                  }`}>
                    {memoryStats.avgConfidence.toFixed(1)}
                  </span>
                </div>
                <Progress 
                  value={memoryStats.avgConfidence} 
                  className="h-1.5 mt-1 bg-slate-700"
                />
              </div>
            </CardContent>
          </Card>

          {/* NNG统计 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Network className="w-3 h-3" />
                NNG导航图
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">节点总数</div>
                  <div className="text-lg font-semibold text-slate-200">{nngStats.totalNodes}</div>
                </div>
                <div className="p-2 bg-slate-700/30 rounded">
                  <div className="text-xs text-slate-500">最大深度</div>
                  <div className="text-lg font-semibold text-slate-200">{nngStats.maxDepth}</div>
                </div>
              </div>

              {/* 深度分布 */}
              {Object.keys(nngStats.depthDistribution).length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs text-slate-500">深度分布</div>
                  {Object.entries(nngStats.depthDistribution)
                    .sort(([a], [b]) => Number(a) - Number(b))
                    .map(([depth, count]) => (
                      <div key={depth} className="flex items-center gap-2">
                        <span className="text-xs text-slate-400 w-12">深度 {depth}</span>
                        <Progress 
                          value={nngStats.totalNodes > 0 ? (count / nngStats.totalNodes) * 100 : 0} 
                          className="flex-1 h-1.5 bg-slate-700"
                        />
                        <span className="text-xs text-slate-500 w-8 text-right">{count}</span>
                      </div>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* DMN状态 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Brain className="w-3 h-3" />
                DMN维护系统
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">运行状态</span>
                <Badge 
                  variant="outline" 
                  className={`text-xs ${
                    dmnState.isRunning 
                      ? 'border-purple-500/50 text-purple-400' 
                      : 'border-slate-600 text-slate-500'
                  }`}
                >
                  {dmnState.isRunning ? '执行中' : '空闲'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">已完成任务</span>
                <span className="text-sm text-slate-300">{dmnState.taskCount}</span>
              </div>
            </CardContent>
          </Card>

          {/* 计数器状态 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Layers className="w-3 h-3" />
                系统计数器
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                  <span className="text-slate-500">记忆计数器</span>
                  <span className="text-slate-300">{systemState.memoryCounter}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                  <span className="text-slate-500">NNG生成器</span>
                  <span className="text-slate-300">{systemState.nngIdGenerator}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                  <span className="text-slate-500">任务计数器</span>
                  <span className="text-slate-300">{systemState.taskCounter}</span>
                </div>
                <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                  <span className="text-slate-500">导航失败</span>
                  <span className={`${systemState.navFailCounter > 0 ? 'text-red-400' : 'text-slate-300'}`}>
                    {systemState.navFailCounter}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 提示信息 */}
          <div className="p-3 bg-slate-800/30 rounded border border-slate-700/50">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-slate-500 mt-0.5" />
              <div className="text-xs text-slate-500">
                <p>系统数据实时更新，供LLM决策使用</p>
                <p className="mt-1">空闲时间达到阈值将触发DMN维护</p>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}

export default SystemMonitor;
