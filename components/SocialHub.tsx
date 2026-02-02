
import React, { useState } from 'react';

export const SocialHub: React.FC = () => {
  const [exporting, setExporting] = useState<string | null>(null);

  const platforms = [
    { 
      id: 'youtube', 
      name: 'YouTube', 
      desc: 'Publish to Studio (Data API v3)', 
      color: 'bg-[#FF0000]', 
      icon: 'M15 10l-6 3V7l6 3z',
      connected: true
    },
    { 
      id: 'instagram', 
      name: 'Instagram', 
      desc: 'Push to Reels (Graph API)', 
      color: 'bg-gradient-to-tr from-[#f9ce34] via-[#ee2a7b] to-[#6228d7]', 
      icon: 'M7 2h10a5 5 0 015 5v10a5 5 0 01-5 5H7a5 5 0 01-5-5V7a5 5 0 015-5zm0 2a3 3 0 00-3 3v10a3 3 0 003 3h10a3 3 0 003-3V7a3 3 0 00-3-3H7z M12 7a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6z M17.5 6.5a1.25 1.25 0 11-2.5 0 1.25 1.25 0 012.5 0z',
      connected: true
    },
    { 
      id: 'tiktok', 
      name: 'TikTok', 
      desc: 'Content Staging Area', 
      color: 'bg-[#000000]', 
      icon: 'M9 8h2v9c0 2 1 3 3 3h1c2 0 3-1 3-3v-2h-2v2c0 1-1 1-1 1h-1c-1 0-1-1-1-1V4h2v2h2V4c0-2-1-3-3-3H9v7z',
      connected: false
    }
  ];

  const handleExport = (id: string) => {
    setExporting(id);
    setTimeout(() => setExporting(null), 3000);
  };

  return (
    <div className="space-y-12">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {platforms.map(p => (
          <div key={p.id} className="obsidian-glass rounded-2xl p-8 border border-white/5 transition-all hover:border-purple-500/30 group">
             <div className="flex justify-between items-start mb-8">
               <div className={`w-14 h-14 ${p.color} rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                 <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                   <path d={p.icon} />
                 </svg>
               </div>
               {p.connected ? (
                 <span className="text-[10px] bg-green-500/20 text-green-400 font-bold px-2 py-1 rounded-full uppercase tracking-tighter border border-green-500/30">Synced</span>
               ) : (
                 <span className="text-[10px] bg-zinc-800 text-zinc-500 font-bold px-2 py-1 rounded-full uppercase tracking-tighter border border-zinc-700">Disconnected</span>
               )}
             </div>
             
             <h3 className="text-xl font-bold mb-2">{p.name}</h3>
             <p className="text-zinc-500 text-sm mb-8 leading-relaxed">{p.desc}</p>
             
             <button
               onClick={() => handleExport(p.id)}
               disabled={!p.connected || exporting !== null}
               className={`w-full py-3 rounded-xl font-bold transition-all ${
                 !p.connected 
                   ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed' 
                   : exporting === p.id
                     ? 'bg-purple-600/50 text-white cursor-wait'
                     : 'bg-white text-black hover:bg-zinc-200 shadow-xl'
               }`}
             >
               {exporting === p.id ? 'Transferring Bytes...' : p.connected ? `Direct Publish` : 'Connect API'}
             </button>
          </div>
        ))}
      </div>

      <div className="obsidian-glass rounded-2xl p-10 border border-purple-500/10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-purple-900/10 via-transparent to-transparent">
         <div className="flex flex-col md:flex-row items-center justify-between gap-10">
           <div className="max-w-xl">
             <h3 className="text-3xl font-bold mb-4 glow-purple-text">Export Master Settings</h3>
             <p className="text-zinc-400 text-lg">
               Finalize your production by configuring high-bitrate encoding presets, custom watermarking, and temporal metadata injection.
             </p>
           </div>
           
           <div className="flex flex-wrap gap-4">
             <div className="obsidian-glass px-6 py-4 rounded-2xl text-center border border-zinc-800">
               <p className="text-xs text-zinc-500 font-bold uppercase mb-1">Target Bitrate</p>
               <span className="text-xl font-mono font-bold text-zinc-200">50 Mbps</span>
             </div>
             <div className="obsidian-glass px-6 py-4 rounded-2xl text-center border border-zinc-800">
               <p className="text-xs text-zinc-500 font-bold uppercase mb-1">Codec</p>
               <span className="text-xl font-mono font-bold text-zinc-200">HEVC (H.265)</span>
             </div>
             <div className="obsidian-glass px-6 py-4 rounded-2xl text-center border border-zinc-800">
               <p className="text-xs text-zinc-500 font-bold uppercase mb-1">Color Depth</p>
               <span className="text-xl font-mono font-bold text-zinc-200">10-bit HDR</span>
             </div>
           </div>
         </div>
      </div>
    </div>
  );
};
