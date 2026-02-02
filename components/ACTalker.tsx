
import React, { useState, useRef, useEffect } from 'react';

export const ACTalker: React.FC = () => {
  const [image, setImage] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (!active || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frame = 0;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw simulated lip-sync wireframe
      ctx.strokeStyle = '#a855f7';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2 + 50;
      const radiusX = 40 + Math.sin(frame * 0.2) * 5;
      const radiusY = 20 + Math.abs(Math.cos(frame * 0.2)) * 15;

      // Lip lines
      ctx.beginPath();
      ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, Math.PI * 2);
      ctx.stroke();

      // Facial grid
      ctx.strokeStyle = 'rgba(168, 85, 247, 0.2)';
      ctx.setLineDash([]);
      for(let i = -3; i <= 3; i++) {
        ctx.beginPath();
        ctx.moveTo(centerX + i * 20, centerY - 100);
        ctx.lineTo(centerX + i * 20, centerY + 100);
        ctx.stroke();
      }

      frame++;
      requestAnimationFrame(animate);
    };

    const animId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animId);
  }, [active]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setImage(ev.target?.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8">
      <div className="flex-1 obsidian-glass rounded-2xl overflow-hidden relative min-h-[500px] border border-zinc-800 group shadow-2xl">
        {image ? (
          <div className="w-full h-full relative">
            <img src={image} className="w-full h-full object-cover" alt="Avatar" />
            <canvas 
              ref={canvasRef} 
              width={600} 
              height={600} 
              className="absolute inset-0 w-full h-full pointer-events-none"
            />
            <div className="absolute bottom-6 left-6 right-6 flex justify-between items-center bg-black/40 backdrop-blur-md p-4 rounded-xl border border-white/10">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${active ? 'bg-green-500 animate-pulse shadow-[0_0_10px_#22c55e]' : 'bg-zinc-600'}`}></div>
                <span className="text-sm font-bold uppercase tracking-widest text-zinc-100">{active ? 'Real-time Sync Active' : 'Engines Standby'}</span>
              </div>
              <button 
                onClick={() => setActive(!active)}
                className={`px-6 py-2 rounded-lg font-bold transition-all ${active ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-purple-600 text-white'}`}
              >
                {active ? 'Terminate Link' : 'Initialize Sync'}
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full p-20 text-center">
             <div className="w-24 h-24 bg-zinc-900 rounded-2xl border-2 border-dashed border-zinc-700 flex items-center justify-center mb-6 group-hover:border-purple-500 transition-colors">
               <svg className="w-10 h-10 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
               </svg>
             </div>
             <h4 className="text-xl font-bold mb-2">Initialize ACTalker</h4>
             <p className="text-zinc-500 mb-8 max-w-xs">Upload a high-fidelity avatar photo to start real-time lip-synchronization profiling.</p>
             <label className="cursor-pointer px-10 py-3 bg-zinc-100 text-black font-bold rounded-xl hover:bg-white transition-all">
                Select Source Asset
                <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
             </label>
          </div>
        )}
      </div>

      <div className="w-full lg:w-80 space-y-6">
        <div className="obsidian-glass rounded-2xl p-6 border border-zinc-800">
           <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-6">Tracking Metadata</h3>
           <div className="space-y-4">
             {[
               { label: 'Lip Landmarks', value: '68 pts' },
               { label: 'Jitter Compensation', value: 'High' },
               { label: 'Micro-Expressions', value: 'Enabled' },
               { label: 'Latency (Local)', value: '18ms' }
             ].map(stat => (
               <div key={stat.label} className="flex justify-between items-end border-b border-zinc-900 pb-2">
                 <span className="text-sm text-zinc-500">{stat.label}</span>
                 <span className="text-sm font-mono text-purple-400 font-bold">{stat.value}</span>
               </div>
             ))}
           </div>
        </div>

        <div className="obsidian-glass rounded-2xl p-6 bg-gradient-to-br from-purple-900/10 to-transparent">
           <h3 className="text-sm font-bold text-purple-400 mb-4">Real-Time Pulse</h3>
           <div className="flex gap-1 h-20 items-end">
             {[...Array(15)].map((_, i) => (
               <div 
                 key={i} 
                 className={`flex-1 bg-purple-500 rounded-t-sm transition-all duration-300 ${active ? 'animate-pulse' : 'opacity-20'}`} 
                 style={{ 
                   height: active ? `${20 + Math.random() * 80}%` : '10%',
                   animationDelay: `${i * 0.1}s`
                 }}
               ></div>
             ))}
           </div>
           <p className="text-[10px] text-zinc-600 mt-4 uppercase font-bold tracking-widest">Warping Coefficents: Nominal</p>
        </div>
      </div>
    </div>
  );
};
