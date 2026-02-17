/**
 * 记忆库视图
 * 
 * 浏览和管理Y层记忆库
 */

import { useState, useEffect } from 'react';
import { Search, Database, Star, Clock, Tag } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

import { getMemoriesByType } from '@/core/memory/memoryStore';
import type { Memory, MemoryType, ValueLevel } from '@/types';

const memoryTypes: MemoryType[] = ['元认知记忆', '高阶整合记忆', '分类记忆', '工作记忆'];
const valueLevels: ValueLevel[] = ['高', '中', '低'];

export function MemoryView() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<MemoryType | 'all'>('all');
  const [selectedLevel, setSelectedLevel] = useState<ValueLevel | 'all'>('all');

  // 加载记忆
  useEffect(() => {
    loadMemories();
  }, [selectedType]);

  const loadMemories = async () => {
    let result: Memory[] = [];
    
    if (selectedType === 'all') {
      // 加载所有类型的记忆
      for (const type of memoryTypes) {
        const typeMemories = await getMemoriesByType(type);
        result = [...result, ...typeMemories];
      }
    } else {
      result = await getMemoriesByType(selectedType);
    }
    
    // 按价值层级过滤
    if (selectedLevel !== 'all') {
      const threshold = selectedLevel === '高' ? 80 : selectedLevel === '中' ? 50 : 0;
      const maxThreshold = selectedLevel === '高' ? 100 : selectedLevel === '中' ? 79 : 49;
      result = result.filter(m => m.置信度 >= threshold && m.置信度 <= maxThreshold);
    }
    
    // 搜索过滤
    if (searchQuery) {
      result = result.filter(m => 
        m.核心内容.用户输入.toLowerCase().includes(searchQuery.toLowerCase()) ||
        m.核心内容.AI响应.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    // 按时间排序
    result.sort((a, b) => new Date(b.记忆时间).getTime() - new Date(a.记忆时间).getTime());
    
    setMemories(result);
  };

  const handleSearch = () => {
    loadMemories();
  };

  const getTypeColor = (type: MemoryType): string => {
    switch (type) {
      case '元认知记忆':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/50';
      case '高阶整合记忆':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
      case '分类记忆':
        return 'bg-green-500/20 text-green-400 border-green-500/50';
      case '工作记忆':
        return 'bg-slate-500/20 text-slate-400 border-slate-500/50';
    }
  };

  const getLevelColor = (confidence: number): string => {
    if (confidence >= 80) return 'text-green-400';
    if (confidence >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="h-full flex flex-col bg-slate-950">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-100">Y层记忆库</h2>
        </div>
        <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
          {memories.length} 条记忆
        </Badge>
      </div>

      {/* 搜索和过滤 */}
      <div className="px-4 py-3 border-b border-slate-800 space-y-3">
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索记忆..."
            className="flex-1 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button
            onClick={handleSearch}
            variant="secondary"
            className="bg-slate-800 hover:bg-slate-700"
          >
            <Search className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as MemoryType | 'all')}
            className="flex-1 bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded px-3 py-1.5"
          >
            <option value="all">所有类型</option>
            {memoryTypes.map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value as ValueLevel | 'all')}
            className="flex-1 bg-slate-800 border border-slate-700 text-slate-300 text-sm rounded px-3 py-1.5"
          >
            <option value="all">所有层级</option>
            {valueLevels.map((level) => (
              <option key={level} value={level}>{level}价值</option>
            ))}
          </select>
        </div>
      </div>

      {/* 记忆列表 */}
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-3">
          {memories.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-slate-500">
              <Database className="w-8 h-8 mb-2 opacity-30" />
              <p className="text-sm">暂无记忆</p>
            </div>
          ) : (
            memories.map((memory) => (
              <Card key={memory.记忆ID} className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getTypeColor(memory.记忆层级)}`}
                      >
                        {memory.记忆层级}
                      </Badge>
                      <span className="text-xs text-slate-500">
                        ID: {memory.记忆ID}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Star className={`w-3 h-3 ${getLevelColor(memory.置信度)}`} />
                      <span className={`text-xs ${getLevelColor(memory.置信度)}`}>
                        {memory.置信度}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div>
                    <p className="text-xs text-slate-500 mb-1">用户:</p>
                    <p className="text-sm text-slate-300 line-clamp-2">
                      {memory.核心内容.用户输入}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-1">AI:</p>
                    <p className="text-sm text-slate-400 line-clamp-3">
                      {memory.核心内容.AI响应}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-700/50">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span className="text-xs text-slate-500">
                      {new Date(memory.记忆时间).toLocaleString()}
                    </span>
                  </div>
                  {memory.关联NNG && memory.关联NNG.length > 0 && (
                    <div className="flex items-center gap-2">
                      <Tag className="w-3 h-3 text-slate-500" />
                      <div className="flex gap-1">
                        {memory.关联NNG.map((nng, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs border-slate-700 text-slate-500">
                            {nng}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export default MemoryView;
