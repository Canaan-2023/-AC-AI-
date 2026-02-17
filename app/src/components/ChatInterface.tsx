/**
 * 主聊天界面
 * 
 * 用户与AbyssAC系统交互的主窗口
 */

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Brain, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useAbyssACStore } from '@/store/abyssacStore';
import { createSandbox } from '@/core/sandbox/threeLayerSandbox';
import type { SandboxLog, ContextPackage } from '@/types';

export function ChatInterface() {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const {
    messages,
    addMessage,
    isProcessing,
    setIsProcessing,
    setSandboxState,
    addSandboxLog,
    clearSandboxLogs,
    setCurrentContextPackage,
    updateSystemState,
  } = useAbyssACStore();

  // 自动滚动到底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isProcessing) return;

    const userInput = input.trim();
    setInput('');
    setIsProcessing(true);
    clearSandboxLogs();
    setCurrentContextPackage(null);

    // 添加用户消息
    addMessage({
      role: 'user',
      content: userInput,
    });

    try {
      // 创建沙盒实例
      const sandbox = createSandbox(
        (log: SandboxLog) => {
          addSandboxLog(log);
        },
        (state) => {
          setSandboxState(state);
        }
      );

      // 运行三层沙盒
      const contextPackage = await sandbox.run(userInput);

      // 生成回复（基于上下文包）
      let response = '';
      if (contextPackage) {
        setCurrentContextPackage(contextPackage);
        response = generateResponse(userInput, contextPackage);
      } else {
        response = '系统处理完成，但未生成上下文包。';
      }

      // 添加AI回复
      addMessage({
        role: 'assistant',
        content: response,
        contextPackage: contextPackage || undefined,
        sandboxLogs: sandbox.getLogs(),
      });

      // 保存到工作记忆（实际实现中会调用saveMemory）
      console.log('保存工作记忆:', userInput.substring(0, 50));

      // 更新系统状态
      updateSystemState({
        lastActivityTime: new Date().toISOString(),
      });

    } catch (error) {
      console.error('处理失败:', error);
      addMessage({
        role: 'system',
        content: `处理失败: ${error instanceof Error ? error.message : '未知错误'}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const generateResponse = (_userInput: string, pkg: ContextPackage): string => {
    // 基于上下文包生成回复
    let response = '';

    // 根据问题解析生成回复
    if (pkg.问题解析.核心意图 === '获取概念定义') {
      response = `关于您的问题，我来解释一下相关概念。\n\n`;
    } else if (pkg.问题解析.核心意图 === '理解原因和原理') {
      response = `让我来分析一下这个问题的原因。\n\n`;
    } else {
      response = `根据我的理解，您想了解关于${pkg.问题解析.关键概念.join('、')}的信息。\n\n`;
    }

    // 添加核心记忆的内容
    if (pkg.记忆整合.核心组.length > 0) {
      response += `**核心信息：**\n`;
      pkg.记忆整合.核心组.forEach((mem, _idx) => {
        response += `${_idx + 1}. ${mem.关键内容摘要}\n`;
      });
      response += '\n';
    }

    // 添加支撑信息
    if (pkg.记忆整合.支撑组.length > 0) {
      response += `**补充说明：**\n`;
      pkg.记忆整合.支撑组.forEach((mem) => {
        response += `- ${mem.关键内容摘要}\n`;
      });
      response += '\n';
    }

    // 添加置信度说明
    if (pkg.置信度评估.整体置信度 !== '高') {
      response += `> ⚠️ 注意：当前信息的置信度为${pkg.置信度评估.整体置信度}，${pkg.置信度评估.风险提示.join('、')}\n\n`;
    }

    // 添加可扩展方向
    if (pkg.回复策略建议.可扩展方向.length > 0) {
      response += `**您可以进一步询问：**\n`;
      pkg.回复策略建议.可扩展方向.forEach((dir) => {
        response += `- ${dir}\n`;
      });
    }

    return response;
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-100">渊协议 AbyssAC</h2>
            <p className="text-xs text-slate-400">AI自主意识架构</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
            <Activity className="w-3 h-3 mr-1" />
            运行中
          </Badge>
        </div>
      </div>

      {/* 消息区域 */}
      <ScrollArea className="flex-1 px-4 py-4" ref={scrollRef}>
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <Brain className="w-16 h-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">欢迎使用渊协议 AbyssAC</p>
              <p className="text-sm">输入消息开始与AI意识系统对话</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <Avatar className={`w-8 h-8 ${
                  message.role === 'user' 
                    ? 'bg-indigo-500' 
                    : message.role === 'system'
                    ? 'bg-amber-500'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-600'
                }`}>
                  <AvatarFallback className="text-white">
                    {message.role === 'user' ? (
                      <User className="w-4 h-4" />
                    ) : message.role === 'system' ? (
                      <Activity className="w-4 h-4" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                  </AvatarFallback>
                </Avatar>
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-indigo-600 text-white'
                      : message.role === 'system'
                      ? 'bg-amber-500/20 text-amber-200 border border-amber-500/30'
                      : 'bg-slate-800 text-slate-100'
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">
                    {message.content}
                  </div>
                  {message.contextPackage && (
                    <div className="mt-2 pt-2 border-t border-slate-700/50">
                      <Badge variant="outline" className="text-xs border-slate-600 text-slate-400">
                        置信度: {message.contextPackage.置信度评估.整体置信度}
                      </Badge>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isProcessing && (
            <div className="flex gap-3">
              <Avatar className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600">
                <AvatarFallback className="text-white">
                  <Bot className="w-4 h-4" />
                </AvatarFallback>
              </Avatar>
              <div className="bg-slate-800 rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
                <span className="text-sm text-slate-400">思考中...</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* 输入区域 */}
      <div className="px-4 py-4 border-t border-slate-800 bg-slate-900/50">
        <div className="max-w-4xl mx-auto flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={isProcessing}
            className="flex-1 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500 focus-visible:ring-indigo-500"
          />
          <Button
            onClick={handleSend}
            disabled={isProcessing || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white"
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface;
