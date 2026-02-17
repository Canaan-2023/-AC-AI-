/**
 * 上下文窗口
 * 
 * 显示当前对话的上下文包详情
 * 这是AbyssAC的核心特色 - 让用户看到AI的"思考过程"
 */

import React from 'react';
import { X, Brain, Route, Database, AlertTriangle, Lightbulb, CheckCircle } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAbyssACStore } from '@/store/abyssacStore';

interface ContextWindowProps {
  onClose?: () => void;
}

export function ContextWindow({ onClose }: ContextWindowProps) {
  const contextPackage = useAbyssACStore((state) => state.currentContextPackage);

  if (!contextPackage) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-500 p-8">
        <Brain className="w-12 h-12 mb-4 opacity-30" />
        <p className="text-sm">暂无上下文数据</p>
        <p className="text-xs mt-1">发送消息后将显示AI的思考过程</p>
      </div>
    );
  }

  const { 
    问题解析, 
    认知路径, 
    记忆整合, 
    缺失信息, 
    置信度评估, 
    回复策略建议 
  } = contextPackage;

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-indigo-400" />
          <h3 className="text-sm font-semibold text-slate-100">上下文窗口</h3>
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

      {/* 内容区域 */}
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-4">
          {/* 问题解析 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Lightbulb className="w-3 h-3" />
                问题解析
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-xs text-slate-500">核心意图：</span>
                <span className="text-sm text-slate-200 ml-1">{问题解析.核心意图}</span>
              </div>
              <div>
                <span className="text-xs text-slate-500">关键概念：</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {问题解析.关键概念.map((concept, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs bg-slate-700 text-slate-300">
                      {concept}
                    </Badge>
                  ))}
                </div>
              </div>
              {问题解析.隐含需求.length > 0 && (
                <div>
                  <span className="text-xs text-slate-500">隐含需求：</span>
                  <ul className="mt-1 space-y-1">
                    {问题解析.隐含需求.map((need, idx) => (
                      <li key={idx} className="text-xs text-slate-400 flex items-center gap-1">
                        <span className="w-1 h-1 bg-slate-500 rounded-full" />
                        {need}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 认知路径 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Route className="w-3 h-3" />
                认知路径
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-1 text-sm">
                {认知路径.路径.map((step, idx) => (
                  <React.Fragment key={idx}>
                    <span className="text-slate-300">{step}</span>
                    {idx < 认知路径.路径.length - 1 && (
                      <span className="text-slate-600 mx-1">→</span>
                    )}
                  </React.Fragment>
                ))}
              </div>
              <p className="text-xs text-slate-500 mt-2">{认知路径.路径说明}</p>
            </CardContent>
          </Card>

          {/* 记忆整合 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Database className="w-3 h-3" />
                记忆整合
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* 核心组 */}
              {记忆整合.核心组.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-indigo-400">核心组</span>
                  <div className="mt-1 space-y-1">
                    {记忆整合.核心组.map((mem, idx) => (
                      <div key={idx} className="p-2 bg-slate-700/50 rounded text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-300">记忆 {mem.记忆ID}</span>
                          <Badge variant="outline" className="text-xs border-indigo-500/50 text-indigo-300">
                            {mem.置信度}
                          </Badge>
                        </div>
                        <p className="text-slate-400 mt-1">{mem.关键内容摘要}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 支撑组 */}
              {记忆整合.支撑组.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-slate-400">支撑组</span>
                  <div className="mt-1 space-y-1">
                    {记忆整合.支撑组.map((mem, idx) => (
                      <div key={idx} className="p-2 bg-slate-700/30 rounded text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">记忆 {mem.记忆ID}</span>
                          <Badge variant="outline" className="text-xs border-slate-600 text-slate-500">
                            {mem.置信度}
                          </Badge>
                        </div>
                        <p className="text-slate-500 mt-1">{mem.关键内容摘要}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 对比组 */}
              {记忆整合.对比组.length > 0 && (
                <div>
                  <span className="text-xs font-medium text-amber-400">对比组</span>
                  <div className="mt-1 space-y-1">
                    {记忆整合.对比组.map((mem, idx) => (
                      <div key={idx} className="p-2 bg-amber-500/10 rounded text-xs border border-amber-500/20">
                        <div className="flex items-center justify-between">
                          <span className="text-amber-300">记忆 {mem.记忆ID}</span>
                          <Badge variant="outline" className="text-xs border-amber-500/50 text-amber-300">
                            {mem.置信度}
                          </Badge>
                        </div>
                        <p className="text-amber-200/70 mt-1">{mem.关键内容摘要}</p>
                        {mem.冲突点 && (
                          <p className="text-amber-400/60 mt-1">冲突: {mem.冲突点}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 缺失信息 */}
          {(缺失信息.已知但未获取.length > 0 || 
            缺失信息.疑似存在.length > 0 || 
            缺失信息.需要澄清.length > 0) && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                  <AlertTriangle className="w-3 h-3" />
                  缺失信息
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {缺失信息.已知但未获取.length > 0 && (
                  <div>
                    <span className="text-xs text-slate-500">已知但未获取：</span>
                    <ul className="mt-1 space-y-1">
                      {缺失信息.已知但未获取.map((item, idx) => (
                        <li key={idx} className="text-xs text-slate-400">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {缺失信息.疑似存在.length > 0 && (
                  <div>
                    <span className="text-xs text-slate-500">疑似存在：</span>
                    <ul className="mt-1 space-y-1">
                      {缺失信息.疑似存在.map((item, idx) => (
                        <li key={idx} className="text-xs text-slate-400">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 置信度评估 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <CheckCircle className="w-3 h-3" />
                置信度评估
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">整体置信度：</span>
                <Badge 
                  className={`text-xs ${
                    置信度评估.整体置信度 === '高' 
                      ? 'bg-green-500/20 text-green-400 border-green-500/50' 
                      : 置信度评估.整体置信度 === '中'
                      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50'
                      : 'bg-red-500/20 text-red-400 border-red-500/50'
                  }`}
                >
                  {置信度评估.整体置信度}
                </Badge>
              </div>
              <p className="text-xs text-slate-400">{置信度评估.依据}</p>
              {置信度评估.风险提示.length > 0 && (
                <div className="mt-2">
                  <span className="text-xs text-amber-500">风险提示：</span>
                  <ul className="mt-1 space-y-1">
                    {置信度评估.风险提示.map((risk, idx) => (
                      <li key={idx} className="text-xs text-amber-400/70">{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 回复策略 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-slate-400 flex items-center gap-2">
                <Lightbulb className="w-3 h-3" />
                回复策略
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <span className="text-xs text-slate-500">推荐角度：</span>
                <span className="text-xs text-slate-300 ml-1">{回复策略建议.推荐角度}</span>
              </div>
              {回复策略建议.重点强调.length > 0 && (
                <div>
                  <span className="text-xs text-slate-500">重点强调：</span>
                  <ul className="mt-1 space-y-1">
                    {回复策略建议.重点强调.map((item, idx) => (
                      <li key={idx} className="text-xs text-slate-400">{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {回复策略建议.可扩展方向.length > 0 && (
                <div>
                  <span className="text-xs text-slate-500">可扩展方向：</span>
                  <ul className="mt-1 space-y-1">
                    {回复策略建议.可扩展方向.map((item, idx) => (
                      <li key={idx} className="text-xs text-slate-400">{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}

export default ContextWindow;
