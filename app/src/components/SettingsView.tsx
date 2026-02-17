/**
 * 设置视图
 * 
 * 配置LLM、系统参数等
 */

import { useState } from 'react';
import { Settings, Server, Key, Thermometer, Hash, TestTube, Save } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { useAbyssACStore } from '@/store/abyssacStore';
import { testLLMConnection } from '@/core/llm/llmInterface';
import type { LLMConfig } from '@/types';

export function SettingsView() {
  const userSettings = useAbyssACStore((state) => state.userSettings);
  const updateLLMConfig = useAbyssACStore((state) => state.updateLLMConfig);
  const updateUserSettings = useAbyssACStore((state) => state.updateUserSettings);
  
  const [llmConfig, setLlmConfig] = useState<LLMConfig>(userSettings.llmConfig);
  const [testStatus, setTestStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [isTesting, setIsTesting] = useState(false);

  const handleSave = () => {
    updateLLMConfig(llmConfig);
    alert('设置已保存');
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestStatus(null);
    
    const result = await testLLMConnection();
    setTestStatus(result);
    setIsTesting(false);
  };

  return (
    <div className="h-full flex flex-col bg-slate-950">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-100">系统设置</h2>
        </div>
      </div>

      {/* 设置内容 */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <div className="max-w-2xl space-y-6">
          {/* LLM配置 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-slate-200 flex items-center gap-2">
                <Server className="w-4 h-4" />
                LLM配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 提供商 */}
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">提供商</Label>
                <select
                  value={llmConfig.provider}
                  onChange={(e) => setLlmConfig({ ...llmConfig, provider: e.target.value as LLMConfig['provider'] })}
                  className="w-full bg-slate-900 border border-slate-700 text-slate-300 text-sm rounded px-3 py-2"
                >
                  <option value="ollama">Ollama (本地)</option>
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="custom">自定义</option>
                </select>
              </div>

              {/* Base URL */}
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">Base URL</Label>
                <div className="flex gap-2">
                  <Input
                    value={llmConfig.baseUrl}
                    onChange={(e) => setLlmConfig({ ...llmConfig, baseUrl: e.target.value })}
                    placeholder="http://localhost:11434"
                    className="flex-1 bg-slate-900 border-slate-700 text-slate-300"
                  />
                </div>
              </div>

              {/* 模型 */}
              <div className="space-y-2">
                <Label className="text-xs text-slate-400">模型</Label>
                <Input
                  value={llmConfig.model}
                  onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                  placeholder="llama3.1"
                  className="bg-slate-900 border-slate-700 text-slate-300"
                />
              </div>

              {/* API Key */}
              {(llmConfig.provider === 'openai' || llmConfig.provider === 'anthropic') && (
                <div className="space-y-2">
                  <Label className="text-xs text-slate-400 flex items-center gap-1">
                    <Key className="w-3 h-3" />
                    API Key
                  </Label>
                  <Input
                    type="password"
                    value={llmConfig.apiKey || ''}
                    onChange={(e) => setLlmConfig({ ...llmConfig, apiKey: e.target.value })}
                    placeholder="sk-..."
                    className="bg-slate-900 border-slate-700 text-slate-300"
                  />
                </div>
              )}

              {/* Temperature */}
              <div className="space-y-2">
                <Label className="text-xs text-slate-400 flex items-center gap-1">
                  <Thermometer className="w-3 h-3" />
                  Temperature
                </Label>
                <Input
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  value={llmConfig.temperature}
                  onChange={(e) => setLlmConfig({ ...llmConfig, temperature: parseFloat(e.target.value) })}
                  className="bg-slate-900 border-slate-700 text-slate-300"
                />
              </div>

              {/* Max Tokens */}
              <div className="space-y-2">
                <Label className="text-xs text-slate-400 flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  Max Tokens
                </Label>
                <Input
                  type="number"
                  min={1}
                  max={8192}
                  value={llmConfig.maxTokens}
                  onChange={(e) => setLlmConfig({ ...llmConfig, maxTokens: parseInt(e.target.value) })}
                  className="bg-slate-900 border-slate-700 text-slate-300"
                />
              </div>

              {/* 测试连接 */}
              <div className="flex items-center gap-2 pt-2">
                <Button
                  onClick={handleTestConnection}
                  disabled={isTesting}
                  variant="outline"
                  className="border-slate-600 text-slate-300 hover:bg-slate-800"
                >
                  <TestTube className="w-4 h-4 mr-2" />
                  {isTesting ? '测试中...' : '测试连接'}
                </Button>
                {testStatus && (
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${
                      testStatus.success 
                        ? 'border-green-500/50 text-green-400' 
                        : 'border-red-500/50 text-red-400'
                    }`}
                  >
                    {testStatus.message}
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 显示设置 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-slate-200">
                显示设置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-300">显示上下文窗口</p>
                  <p className="text-xs text-slate-500">在侧边栏显示AI的思考过程</p>
                </div>
                <Switch
                  checked={userSettings.showContextWindow}
                  onCheckedChange={(checked) => updateUserSettings({ showContextWindow: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-300">显示系统监控</p>
                  <p className="text-xs text-slate-500">在侧边栏显示系统运行数据</p>
                </div>
                <Switch
                  checked={userSettings.showSystemMonitor}
                  onCheckedChange={(checked) => updateUserSettings({ showSystemMonitor: checked })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-300">显示沙盒日志</p>
                  <p className="text-xs text-slate-500">在侧边栏显示三层沙盒执行日志</p>
                </div>
                <Switch
                  checked={userSettings.showSandboxLogs}
                  onCheckedChange={(checked) => updateUserSettings({ showSandboxLogs: checked })}
                />
              </div>
            </CardContent>
          </Card>

          {/* DMN设置 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-sm font-medium text-slate-200">
                DMN维护系统
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-300">启用DMN维护</p>
                  <p className="text-xs text-slate-500">空闲时自动执行记忆整合和优化</p>
                </div>
                <Switch
                  checked={userSettings.dmNMaintenance}
                  onCheckedChange={(checked) => updateUserSettings({ dmNMaintenance: checked })}
                />
              </div>
            </CardContent>
          </Card>

          {/* 保存按钮 */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              className="bg-indigo-600 hover:bg-indigo-700 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              保存设置
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsView;
