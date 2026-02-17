/**
 * 侧边栏导航
 * 
 * 切换不同视图：聊天、记忆库、NNG图、监控、设置
 */

import React from 'react';
import { 
  MessageSquare, 
  Database, 
  Network, 
  Activity, 
  Settings,
  Brain,
  Github,
  Mail
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAbyssACStore } from '@/store/abyssacStore';
import type { ViewMode } from '@/types';
import { SYSTEM_INFO } from '@/config/system';

interface NavItem {
  id: ViewMode;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { id: 'chat', label: '对话', icon: MessageSquare },
  { id: 'memory', label: '记忆库', icon: Database },
  { id: 'nng', label: 'NNG图', icon: Network },
  { id: 'monitor', label: '监控', icon: Activity },
  { id: 'config', label: '设置', icon: Settings },
];

interface SidebarProps {
  onViewChange?: (view: ViewMode) => void;
}

export function Sidebar({ onViewChange }: SidebarProps) {
  const currentView = useAbyssACStore((state) => state.currentView);
  const setCurrentView = useAbyssACStore((state) => state.setCurrentView);

  const handleViewChange = (view: ViewMode) => {
    setCurrentView(view);
    onViewChange?.(view);
  };

  return (
    <div className="w-16 h-full bg-slate-950 border-r border-slate-800 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-slate-800">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
      </div>

      {/* 导航项 */}
      <nav className="flex-1 py-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => handleViewChange(item.id)}
              className={cn(
                'w-full px-4 py-3 flex flex-col items-center gap-1 transition-colors',
                'hover:bg-slate-900',
                isActive && 'bg-slate-900 border-l-2 border-indigo-500'
              )}
              title={item.label}
            >
              <Icon 
                className={cn(
                  'w-5 h-5',
                  isActive ? 'text-indigo-400' : 'text-slate-500'
                )} 
              />
              <span 
                className={cn(
                  'text-[10px]',
                  isActive ? 'text-indigo-400' : 'text-slate-500'
                )}
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* 底部链接 */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex justify-center text-slate-500 hover:text-slate-300 transition-colors"
          title="GitHub"
        >
          <Github className="w-4 h-4" />
        </a>
        <a
          href={`mailto:${SYSTEM_INFO.contact}`}
          className="flex justify-center text-slate-500 hover:text-slate-300 transition-colors"
          title="联系作者"
        >
          <Mail className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
}

export default Sidebar;
