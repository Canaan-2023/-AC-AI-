/**
 * 沙盒日志组件
 * 
 * 显示三层沙盒的执行日志
 */

import { X, Layers, ArrowRight, AlertCircle, CheckCircle, Terminal } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { useAbyssACStore } from '@/store/abyssacStore';
import type { SandboxLog } from '@/types';

interface SandboxLogsProps {
  onClose?: () => void;
}

export function SandboxLogs({ onClose }: SandboxLogsProps) {
  const logs = useAbyssACStore((state) => state.sandboxLogs);
  const sandboxState = useAbyssACStore((state) => state.sandboxState);

  const getLayerName = (layer: number): string => {
    switch (layer) {
      case 1: return 'NNG导航';
      case 2: return '记忆筛选';
      case 3: return '上下文组装';
      default: return '未知';
    }
  };

  const getTypeIcon = (type: SandboxLog['type']) => {
    switch (type) {
      case 'input':
        return <ArrowRight className="w-3 h-3 text-blue-400" />;
      case 'output':
        return <ArrowRight className="w-3 h-3 text-green-400" />;
      case 'system':
        return <CheckCircle className="w-3 h-3 text-slate-400" />;
      case 'error':
        return <AlertCircle className="w-3 h-3 text-red-400" />;
    }
  };

  const getTypeColor = (type: SandboxLog['type']): string => {
    switch (type) {
      case 'input':
        return 'border-l-blue-500';
      case 'output':
        return 'border-l-green-500';
      case 'system':
        return 'border-l-slate-500';
      case 'error':
        return 'border-l-red-500';
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-100">沙盒日志</h3>
          {sandboxState && (
            <Badge variant="outline" className="text-xs border-slate-700 text-slate-500">
              <Layers className="w-3 h-3 mr-1" />
              第{sandboxState.currentLayer}层
            </Badge>
          )}
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* 日志内容 */}
      <ScrollArea className="flex-1 px-4 py-4">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-500">
            <Terminal className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-xs">暂无日志</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs.map((log, idx) => (
              <div
                key={idx}
                className={`p-3 bg-slate-800/50 rounded border-l-2 ${getTypeColor(log.type)}`}
              >
                <div className="flex items-start gap-2">
                  {getTypeIcon(log.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge 
                        variant="outline" 
                        className="text-xs border-slate-700 text-slate-500"
                      >
                        L{log.layer}
                      </Badge>
                      <span className="text-xs text-slate-500">
                        R{log.round}
                      </span>
                      <span className="text-xs text-slate-600">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-slate-300 break-words">
                      {log.content}
                    </p>
                    {log.paths && log.paths.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {log.paths.map((path, pidx) => (
                          <div 
                            key={pidx}
                            className="text-xs font-mono text-slate-500 bg-slate-900/50 px-2 py-1 rounded truncate"
                          >
                            {path}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* 底部状态 */}
      {sandboxState && (
        <div className="px-4 py-2 border-t border-slate-800 bg-slate-900/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-500">
              当前: {getLayerName(sandboxState.currentLayer)}
            </span>
            <span className="text-slate-500">
              轮次: {sandboxState.round}
            </span>
          </div>
          {sandboxState.isComplete && (
            <div className="mt-1 text-xs text-green-400">
              ✓ 沙盒执行完成
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default SandboxLogs;
