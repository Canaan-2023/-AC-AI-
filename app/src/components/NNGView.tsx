/**
 * NNG导航图视图
 * 
 * 可视化展示NNG概念网络
 */

import { useState, useEffect } from 'react';
import { Network, Search, ChevronRight, ChevronDown, Star } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { loadNNGNode, loadRootNode, getChildNodes, getNNGStats } from '@/core/nng/nngStore';
import type { NNGRoot } from '@/types';

interface TreeNode {
  id: string;
  content: string;
  confidence: number;
  children: TreeNode[];
  expanded: boolean;
  loaded: boolean;
}

export function NNGView() {
  const [, setRootData] = useState<NNGRoot | null>(null);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({ totalNodes: 0, maxDepth: 0 });

  // 加载根节点
  useEffect(() => {
    loadRootData();
    setStats(getNNGStats());
  }, []);

  const loadRootData = async () => {
    const root = await loadRootNode();
    setRootData(root);
    
    // 构建树形数据
    const tree: TreeNode[] = root.一级节点.map((nodeStr) => {
      const [id, content] = nodeStr.split('（');
      return {
        id: id.trim(),
        content: content ? content.replace('）', '') : '',
        confidence: 80,
        children: [],
        expanded: false,
        loaded: false,
      };
    });
    
    setTreeData(tree);
  };

  const loadNodeChildren = async (node: TreeNode) => {
    if (node.loaded) return;
    
    const childIds = await getChildNodes(node.id);
    const children: TreeNode[] = [];
    
    for (const childId of childIds) {
      const nngNode = await loadNNGNode(childId);
      if (nngNode) {
        children.push({
          id: childId,
          content: nngNode.内容,
          confidence: nngNode.置信度,
          children: [],
          expanded: false,
          loaded: false,
        });
      }
    }
    
    node.children = children;
    node.loaded = true;
    setTreeData([...treeData]);
  };

  const toggleNode = async (node: TreeNode) => {
    if (!node.expanded) {
      await loadNodeChildren(node);
    }
    node.expanded = !node.expanded;
    setTreeData([...treeData]);
  };

  const renderTreeNode = (node: TreeNode, depth: number = 0) => {
    const paddingLeft = depth * 20;
    
    return (
      <div key={node.id}>
        <div
          className="flex items-center gap-2 py-2 px-2 hover:bg-slate-800/50 rounded cursor-pointer group"
          style={{ paddingLeft: `${paddingLeft + 8}px` }}
          onClick={() => toggleNode(node)}
        >
          <button className="p-0.5 hover:bg-slate-700 rounded">
            {node.children.length > 0 || !node.loaded ? (
              node.expanded ? (
                <ChevronDown className="w-4 h-4 text-slate-500" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-500" />
              )
            ) : (
              <span className="w-4" />
            )}
          </button>
          <span className="text-sm font-mono text-slate-500 w-12">{node.id}</span>
          <span className="text-sm text-slate300 flex-1 truncate">{node.content}</span>
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Star className="w-3 h-3 text-slate-500" />
            <span className="text-xs text-slate-500">{node.confidence}</span>
          </div>
        </div>
        {node.expanded && node.children.length > 0 && (
          <div>
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-slate-950">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-3">
          <Network className="w-5 h-5 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-100">NNG导航图</h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
            {stats.totalNodes} 节点
          </Badge>
          <Badge variant="outline" className="text-xs border-slate-700 text-slate-400">
            深度 {stats.maxDepth}
          </Badge>
        </div>
      </div>

      {/* 搜索 */}
      <div className="px-4 py-3 border-b border-slate-800">
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索节点..."
            className="flex-1 bg-slate-800 border-slate-700 text-slate-100 placeholder:text-slate-500"
          />
          <Button
            variant="secondary"
            className="bg-slate-800 hover:bg-slate-700"
          >
            <Search className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* 树形视图 */}
      <ScrollArea className="flex-1">
        <div className="p-4">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-2">
              {treeData.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-slate-500">
                  <Network className="w-8 h-8 mb-2 opacity-30" />
                  <p className="text-sm">加载中...</p>
                </div>
              ) : (
                <div>
                  {treeData.map((node) => renderTreeNode(node))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}

export default NNGView;
