/**
 * AbyssAC - 渊协议
 * AI人工意识自主进化架构
 * 
 * 主应用组件
 */

import { useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { ChatInterface } from '@/components/ChatInterface';
import { ContextWindow } from '@/components/ContextWindow';
import { SystemMonitor } from '@/components/SystemMonitor';
import { SandboxLogs } from '@/components/SandboxLogs';
import { MemoryView } from '@/components/MemoryView';
import { NNGView } from '@/components/NNGView';
import { SettingsView } from '@/components/SettingsView';
import { useAbyssACStore } from '@/store/abyssacStore';

function App() {
  const currentView = useAbyssACStore((state) => state.currentView);
  const userSettings = useAbyssACStore((state) => state.userSettings);
  const incrementIdleTime = useAbyssACStore((state) => state.incrementIdleTime);
  const resetIdleTime = useAbyssACStore((state) => state.resetIdleTime);

  // 空闲时间追踪
  useEffect(() => {
    const interval = setInterval(() => {
      incrementIdleTime(1000);
    }, 1000);

    // 用户活动时重置空闲时间
    const handleActivity = () => {
      resetIdleTime();
    };

    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);

    return () => {
      clearInterval(interval);
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, [incrementIdleTime, resetIdleTime]);

  // 渲染主内容区
  const renderMainContent = () => {
    switch (currentView) {
      case 'chat':
        return <ChatInterface />;
      case 'memory':
        return <MemoryView />;
      case 'nng':
        return <NNGView />;
      case 'monitor':
        return <SystemMonitor />;
      case 'config':
        return <SettingsView />;
      default:
        return <ChatInterface />;
    }
  };

  // 计算侧边栏宽度
  const getRightSidebarWidth = () => {
    let width = 0;
    if (userSettings.showContextWindow) width += 320;
    if (userSettings.showSystemMonitor) width += 280;
    if (userSettings.showSandboxLogs) width += 320;
    return width;
  };

  const rightSidebarWidth = getRightSidebarWidth();

  return (
    <div className="h-screen w-screen bg-slate-950 flex overflow-hidden">
      {/* 左侧导航栏 */}
      <Sidebar />

      {/* 主内容区 */}
      <div 
        className="flex-1 transition-all duration-300"
        style={{ 
          marginRight: currentView === 'chat' ? rightSidebarWidth : 0 
        }}
      >
        {renderMainContent()}
      </div>

      {/* 右侧边栏 - 仅在对话视图显示 */}
      {currentView === 'chat' && rightSidebarWidth > 0 && (
        <div 
          className="fixed right-0 top-0 h-full bg-slate-900 border-l border-slate-800 flex transition-all duration-300"
          style={{ width: rightSidebarWidth }}
        >
          {userSettings.showContextWindow && (
            <div className="w-80 border-r border-slate-800">
              <ContextWindow />
            </div>
          )}
          {userSettings.showSystemMonitor && (
            <div className="w-70 border-r border-slate-800">
              <SystemMonitor />
            </div>
          )}
          {userSettings.showSandboxLogs && (
            <div className="w-80">
              <SandboxLogs />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
