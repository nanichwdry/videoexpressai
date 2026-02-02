
import React from 'react';
import { DashboardTab } from '../types';

interface SidebarProps {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: DashboardTab.GENERATOR, label: 'Generator', icon: 'M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' },
    { id: DashboardTab.VOICE_LAB, label: 'Voice Lab', icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z' },
    { id: DashboardTab.ACTALKER, label: 'ACTalker', icon: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    { id: DashboardTab.TRAINING, label: 'LoRA Studio', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.691.31a2 2 0 01-1.782 0l-.691-.31a6 6 0 00-3.86-.517l-2.387.477a2 2 0 00-1.022.547l-.547 1.022a2 2 0 00.547 2.387l.477 2.387a6 6 0 00.517 3.86l.31.691a2 2 0 010 1.782l-.31.691a6 6 0 00-.517 3.86l.477 2.387a2 2 0 002.387.547l1.022-.547a2 2 0 00.547-1.022l.477-2.387a6 6 0 00-.517-3.86l-.31-.691a2 2 0 010-1.782l.31-.691a6 6 0 00.517-3.86l-.477-2.387z' }, // Note: simplified icon path
    { id: DashboardTab.EXPORT, label: 'Export', icon: 'M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z' }
  ];

  return (
    <aside className="w-64 obsidian-glass border-r border-zinc-800 flex flex-col z-10">
      <div className="p-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.5)]">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="text-xl font-bold tracking-tighter text-white">VideoExpress</span>
        </div>
      </div>

      <nav className="flex-1 px-4 mt-6 space-y-2">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 ${
              activeTab === item.id 
                ? 'bg-purple-600/20 text-purple-400 border border-purple-500/20 shadow-[0_0_10px_rgba(168,85,247,0.1)]' 
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5'
            }`}
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={item.icon} />
            </svg>
            <span className="font-medium">{item.label}</span>
            {activeTab === item.id && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_8px_#a855f7]"></div>}
          </button>
        ))}
      </nav>

      <div className="p-6">
        <div className="obsidian-glass rounded-xl p-4 border border-zinc-800">
          <p className="text-xs text-zinc-500 uppercase font-semibold tracking-wider mb-2">GPU Credits</p>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-bold text-zinc-300">84%</span>
            <span className="text-xs text-zinc-500">1.2k / 1.5k</span>
          </div>
          <div className="w-full bg-zinc-900 rounded-full h-1.5 overflow-hidden">
            <div className="bg-purple-500 h-full w-[84%] shadow-[0_0_8px_#a855f7]"></div>
          </div>
        </div>
      </div>
    </aside>
  );
};
