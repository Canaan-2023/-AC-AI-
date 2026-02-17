/**
 * LLM集成接口
 * 
 * 支持多种LLM提供商：Ollama、OpenAI、Anthropic等
 */

import type { LLMConfig, LLMRequest, LLMResponse, LLMMessage } from '@/types';
import { DEFAULT_LLM_CONFIG } from '@/config/system';

// 当前LLM配置
let currentConfig: LLMConfig = { ...DEFAULT_LLM_CONFIG };

/**
 * 设置LLM配置
 */
export function setLLMConfig(config: Partial<LLMConfig>): void {
  currentConfig = { ...currentConfig, ...config };
}

/**
 * 获取当前LLM配置
 */
export function getLLMConfig(): LLMConfig {
  return { ...currentConfig };
}

/**
 * 调用LLM
 */
export async function callLLM(request: LLMRequest): Promise<LLMResponse> {
  switch (currentConfig.provider) {
    case 'ollama':
      return callOllama(request);
    case 'openai':
      return callOpenAI(request);
    case 'anthropic':
      return callAnthropic(request);
    case 'custom':
      return callCustom(request);
    default:
      return {
        content: '',
        error: `不支持的LLM提供商: ${currentConfig.provider}`,
      };
  }
}

/**
 * 调用Ollama本地模型
 */
async function callOllama(request: LLMRequest): Promise<LLMResponse> {
  try {
    const response = await fetch(`${currentConfig.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: currentConfig.model,
        messages: request.messages,
        stream: false,
        options: {
          temperature: request.temperature ?? currentConfig.temperature,
          num_predict: request.maxTokens ?? currentConfig.maxTokens,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`Ollama API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.message?.content || '',
      usage: {
        promptTokens: data.prompt_eval_count || 0,
        completionTokens: data.eval_count || 0,
        totalTokens: (data.prompt_eval_count || 0) + (data.eval_count || 0),
      },
    };
  } catch (error) {
    console.error('[LLM] Ollama调用失败:', error);
    return {
      content: '',
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
}

/**
 * 调用OpenAI API
 */
async function callOpenAI(request: LLMRequest): Promise<LLMResponse> {
  try {
    const response = await fetch(`${currentConfig.baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentConfig.apiKey}`,
      },
      body: JSON.stringify({
        model: currentConfig.model,
        messages: request.messages,
        temperature: request.temperature ?? currentConfig.temperature,
        max_tokens: request.maxTokens ?? currentConfig.maxTokens,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.choices?.[0]?.message?.content || '',
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    };
  } catch (error) {
    console.error('[LLM] OpenAI调用失败:', error);
    return {
      content: '',
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
}

/**
 * 调用Anthropic Claude API
 */
async function callAnthropic(request: LLMRequest): Promise<LLMResponse> {
  try {
    const response = await fetch(`${currentConfig.baseUrl}/v1/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': currentConfig.apiKey || '',
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: currentConfig.model,
        messages: request.messages.filter(m => m.role !== 'system'),
        system: request.messages.find(m => m.role === 'system')?.content,
        temperature: request.temperature ?? currentConfig.temperature,
        max_tokens: request.maxTokens ?? currentConfig.maxTokens,
      }),
    });

    if (!response.ok) {
      throw new Error(`Anthropic API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.content?.[0]?.text || '',
      usage: {
        promptTokens: data.usage?.input_tokens || 0,
        completionTokens: data.usage?.output_tokens || 0,
        totalTokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0),
      },
    };
  } catch (error) {
    console.error('[LLM] Anthropic调用失败:', error);
    return {
      content: '',
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
}

/**
 * 调用自定义API
 */
async function callCustom(request: LLMRequest): Promise<LLMResponse> {
  try {
    const response = await fetch(`${currentConfig.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(currentConfig.apiKey && { 'Authorization': `Bearer ${currentConfig.apiKey}` }),
      },
      body: JSON.stringify({
        model: currentConfig.model,
        messages: request.messages,
        temperature: request.temperature ?? currentConfig.temperature,
        max_tokens: request.maxTokens ?? currentConfig.maxTokens,
      }),
    });

    if (!response.ok) {
      throw new Error(`Custom API错误: ${response.status}`);
    }

    const data = await response.json();
    return {
      content: data.choices?.[0]?.message?.content || data.response || '',
      usage: {
        promptTokens: data.usage?.prompt_tokens || 0,
        completionTokens: data.usage?.completion_tokens || 0,
        totalTokens: data.usage?.total_tokens || 0,
      },
    };
  } catch (error) {
    console.error('[LLM] Custom调用失败:', error);
    return {
      content: '',
      error: error instanceof Error ? error.message : '未知错误',
    };
  }
}

/**
 * 测试LLM连接
 */
export async function testLLMConnection(): Promise<{ success: boolean; message: string }> {
  try {
    const response = await callLLM({
      messages: [
        { role: 'user', content: 'Hello' },
      ],
      maxTokens: 10,
    });

    if (response.error) {
      return { success: false, message: response.error };
    }

    return { success: true, message: '连接成功' };
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : '连接失败',
    };
  }
}

/**
 * 构建系统消息
 */
export function buildSystemMessage(content: string): LLMMessage {
  return { role: 'system', content };
}

/**
 * 构建用户消息
 */
export function buildUserMessage(content: string): LLMMessage {
  return { role: 'user', content };
}

/**
 * 构建助手消息
 */
export function buildAssistantMessage(content: string): LLMMessage {
  return { role: 'assistant', content };
}

/**
 * 格式化提示词（替换占位符）
 */
export function formatPrompt(
  template: string,
  variables: Record<string, string>
): string {
  let result = template;
  for (const [key, value] of Object.entries(variables)) {
    result = result.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }
  return result;
}

/**
 * 解析LLM输出的路径
 */
export function parsePathsFromLLMOutput(output: string): {
  nngPaths: string[];
  memoryPaths: string[];
  note: string;
} {
  const lines = output.split('\n');
  const nngPaths: string[] = [];
  const memoryPaths: string[] = [];
  let note = '';

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('nng/')) {
      nngPaths.push(trimmed);
    } else if (trimmed.startsWith('Y层记忆库/')) {
      memoryPaths.push(trimmed);
    } else if (trimmed.startsWith('笔记：')) {
      note = trimmed.replace('笔记：', '');
    }
  }

  return { nngPaths, memoryPaths, note };
}
