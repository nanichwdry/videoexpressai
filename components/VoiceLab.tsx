
import React, { useState } from 'react';

export const VoiceLab: React.FC = () => {
  const [cloning, setCloning] = useState<boolean>(false);
  const [selectedPreset, setSelectedPreset] = useState<string>('Enthusiastic');
  const [recorded, setRecorded] = useState<boolean>(false);

  const presets = [
    'Enthusiastic', 'Melancholic', 'Authoritative', 'Whispering', 'Aggressive', 
    'Seductive', 'Cyborg', 'Distant', 'Child-like', 'Elderly', 'Cinematic Narrator'
  ];

  const handleClone = () => {
    setCloning(true);
    setTimeout(() => {
      setCloning(false);
      setRecorded(true);
    }, 3000);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div className="obsidian-glass rounded-2xl p-8 border border-purple-500/10">
        <h3 className="text-2xl font-bold mb-6 glow-purple-text">Qwen3 Voice Cloning</h3>
        <p className="text-zinc-400 mb-8 leading-relaxed">
          Upload or record a 3-second neural signature to synthesize a perfect digital twin of any vocal profile.
        </p>
        
        <div className="relative group overflow-hidden bg-zinc-900/50 rounded-2xl border border-zinc-800 p-10 text-center transition-all hover:border-purple-500/30">
          {!recorded ? (
            <div className="space-y-6">
              <div className="w-20 h-20 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-4 border border-purple-500/20 group-hover:scale-110 transition-transform">
                <svg className="w-10 h-10 text-purple-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </div>
              <button 
                onClick={handleClone}
                disabled={cloning}
                className="px-6 py-2 bg-purple-600 text-white rounded-lg font-bold shadow-[0_0_15px_rgba(168,85,247,0.3)] hover:bg-purple-500 transition-all disabled:opacity-50"
              >
                {cloning ? 'Capturing Neural Profile...' : 'Begin Voice Capture'}
              </button>
              <p className="text-xs text-zinc-600 uppercase tracking-widest font-bold">Minimum 3.0s sample required</p>
            </div>
          ) : (
            <div className="animate-in fade-in zoom-in duration-500">
               <div className="flex items-center justify-center gap-2 mb-6 text-green-400 font-bold">
                 <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                 </svg>
                 Signature Captured
               </div>
               <div className="flex gap-1 justify-center h-8 items-end">
                 {[...Array(20)].map((_, i) => (
                   <div key={i} className="w-1 bg-purple-500/60 rounded-full" style={{ height: `${Math.random() * 100}%` }}></div>
                 ))}
               </div>
               <button onClick={() => setRecorded(false)} className="mt-8 text-xs text-zinc-500 hover:text-purple-400 underline">Reset Signature</button>
            </div>
          )}
        </div>
      </div>

      <div className="obsidian-glass rounded-2xl p-8">
        <h3 className="text-2xl font-bold mb-6 text-zinc-100">Emotional Intelligence</h3>
        <p className="text-zinc-400 mb-8 leading-relaxed">
          Inject complex emotive vectors using our proprietary Qwen-base emotional preset library.
        </p>

        <div className="space-y-6">
          <label className="text-xs text-zinc-500 uppercase tracking-widest font-bold block">100+ Multi-Dimensional Presets</label>
          <div className="grid grid-cols-2 gap-3">
            {presets.map(p => (
              <button
                key={p}
                onClick={() => setSelectedPreset(p)}
                className={`text-left px-4 py-3 rounded-xl border transition-all text-sm font-medium ${
                  selectedPreset === p 
                    ? 'bg-purple-600/10 border-purple-500/40 text-purple-400 shadow-[inset_0_0_10px_rgba(168,85,247,0.05)]' 
                    : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:border-zinc-700'
                }`}
              >
                {p}
              </button>
            ))}
            <button className="text-center px-4 py-3 rounded-xl bg-zinc-800/50 text-zinc-400 text-xs font-bold border border-zinc-700/50 hover:bg-zinc-800 transition-all">
              Load More...
            </button>
          </div>

          <div className="mt-8 p-4 bg-purple-950/20 rounded-xl border border-purple-500/20">
            <h4 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-2 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"></span>
              Live Synthesizer Status
            </h4>
            <p className="text-sm text-zinc-400">Current Vector: <span className="text-zinc-200 font-bold">{selectedPreset}</span></p>
          </div>
        </div>
      </div>
    </div>
  );
};
