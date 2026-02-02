
import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { DashboardTab } from './types';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<DashboardTab>(DashboardTab.GENERATOR);
  const [apiKeySet, setApiKeySet] = useState<boolean>(false);

  useEffect(() => {
    // Check for API key presence if needed for Veo specific flows
    const checkKey = async () => {
      if ((window as any).aistudio?.hasSelectedApiKey) {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        setApiKeySet(hasKey);
      } else {
        // Fallback for environment where process.env.API_KEY is just used
        setApiKeySet(true);
      }
    };
    checkKey();
  }, []);

  const handleSelectKey = async () => {
    if ((window as any).aistudio?.openSelectKey) {
      await (window as any).aistudio.openSelectKey();
      setApiKeySet(true);
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#030303] text-zinc-100 overflow-hidden font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 relative overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-900/10 via-zinc-950 to-zinc-950">
        {!apiKeySet && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="obsidian-glass p-8 rounded-2xl max-w-md text-center">
              <h2 className="text-2xl font-bold mb-4 text-purple-400">Initialize Engine</h2>
              <p className="text-zinc-400 mb-6">VideoExpress AI requires a valid Cloud Project API Key for high-fidelity rendering.</p>
              <button 
                onClick={handleSelectKey}
                className="w-full py-3 bg-purple-600 hover:bg-purple-500 rounded-lg font-semibold transition-all glow-purple"
              >
                Select API Key
              </button>
              <a 
                href="https://ai.google.dev/gemini-api/docs/billing" 
                target="_blank" 
                className="mt-4 block text-xs text-zinc-500 hover:text-purple-400 underline"
              >
                Learn about Billing Requirements
              </a>
            </div>
          </div>
        )}

        <div className="max-w-7xl mx-auto">
          <header className="flex justify-between items-center mb-10">
            <div>
              <h1 className="text-4xl font-bold tracking-tight glow-purple-text">
                {activeTab === DashboardTab.GENERATOR && 'Wan 2.5 Control Panel'}
                {activeTab === DashboardTab.VOICE_LAB && 'Qwen3 Voice Lab'}
                {activeTab === DashboardTab.ACTALKER && 'ACTalker Real-Time Preview'}
                {activeTab === DashboardTab.TRAINING && 'LoRA Training Studio'}
                {activeTab === DashboardTab.EXPORT && 'Export & Social Hub'}
              </h1>
              <p className="text-zinc-500 mt-1">VideoExpress AI • Enterprise Production Suite</p>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="px-4 py-2 obsidian-glass rounded-full border border-purple-500/30 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium text-zinc-300">Engine Online</span>
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-600 to-fuchsia-500 flex items-center justify-center text-sm font-bold border border-white/20">
                JD
              </div>
            </div>
          </header>

          <Dashboard activeTab={activeTab} />
        </div>
      </main>
    </div>
  );
};

export default App;
