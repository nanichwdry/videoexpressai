
import React, { useState } from 'react';
import { Resolution } from '../types';
import { createJob, enhancePrompt } from '../src/api/client';
import { useJob } from '../src/hooks/useJob';

export const WanControlPanel: React.FC = () => {
  const [resolution, setResolution] = useState<Resolution>('1080p');
  const [motion, setMotion] = useState<number>(50);
  const [prompt, setPrompt] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [enhancing, setEnhancing] = useState(false);
  const { job, error } = useJob(jobId);

  const handleEnhancePrompt = async () => {
    if (!prompt) return;
    setEnhancing(true);
    try {
      const result = await enhancePrompt(prompt);
      if (result.used_gemini) {
        setPrompt(result.enhanced_prompt);
      }
    } catch (err) {
      console.error('Failed to enhance prompt:', err);
    } finally {
      setEnhancing(false);
    }
  };

  const handleGenerate = async () => {
    try {
      const { job_id } = await createJob('RENDER', {
        prompt,
        duration: 5,
        resolution,
        motion_intensity: motion / 100
      });
      setJobId(job_id);
    } catch (err) {
      console.error('Failed to create job:', err);
    }
  };

  const generating = job?.status === 'QUEUED' || job?.status === 'RUNNING';
  const videoUrl = job?.output_urls?.[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-6">
        <div className="obsidian-glass rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500 to-transparent opacity-50"></div>
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-purple-500"></span>
            Global Prompt Interface
          </h3>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A cinematic drone shot of a futuristic obsidian city during a purple lightning storm..."
            className="w-full h-48 bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-purple-500/50 transition-colors"
          />
          <div className="mt-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <button
                onClick={handleEnhancePrompt}
                disabled={enhancing || !prompt}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  enhancing || !prompt
                    ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                    : 'bg-zinc-800 hover:bg-zinc-700 text-purple-400 border border-purple-500/30'
                }`}
              >
                {enhancing ? '✨ Enhancing...' : '✨ AI Enhance'}
              </button>
              <span className="text-xs text-zinc-500 italic">Gemini-powered prompt optimization</span>
            </div>
            <button
              onClick={handleGenerate}
              disabled={generating || !prompt}
              className={`px-8 py-3 rounded-xl font-bold transition-all ${
                generating || !prompt
                  ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]'
              }`}
            >
              {generating ? 'Engine Rendering...' : 'Ignite Engine'}
            </button>
          </div>
        </div>

        <div className="obsidian-glass rounded-2xl p-6 h-[400px] flex items-center justify-center border border-dashed border-zinc-800">
           {error && (
             <div className="text-center text-red-400">
               <p className="font-semibold">Error: {error}</p>
               {job?.error && (
                 <p className="text-sm mt-2 text-zinc-500">Code: {job.error.code}</p>
               )}
             </div>
           )}
           {generating ? (
             <div className="text-center">
               <div className="relative w-24 h-24 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full border-4 border-purple-500/20"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-purple-500 border-t-transparent animate-spin"></div>
               </div>
               <p className="text-purple-400 font-medium animate-pulse">Computing Temporal Coherence...</p>
               <p className="text-zinc-500 text-sm mt-2">{job?.progress || 0}% complete</p>
               {job?.status_hint === 'warming_gpu' && (
                 <p className="text-yellow-400 text-xs mt-2">⚡ Warming GPU (first run ~30s)</p>
               )}
               <div className="w-64 h-2 bg-zinc-800 rounded-full mt-4 mx-auto overflow-hidden">
                 <div 
                   className="h-full bg-gradient-to-r from-purple-600 to-fuchsia-500 transition-all duration-300"
                   style={{ width: `${job?.progress || 0}%` }}
                 ></div>
               </div>
             </div>
           ) : videoUrl ? (
             <video src={videoUrl} controls className="max-w-full max-h-full rounded-lg" />
           ) : (
             <div className="text-center text-zinc-600">
               <svg className="w-16 h-16 mx-auto mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
               </svg>
               <p>Preview will manifest here after ignition</p>
             </div>
           )}
        </div>
      </div>

      <div className="space-y-6">
        <div className="obsidian-glass rounded-2xl p-6">
          <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            Engine Parameters
          </h3>

          <div className="space-y-8">
            <div>
              <label className="text-sm text-zinc-400 block mb-3 font-medium uppercase tracking-wider">Target Resolution</label>
              <div className="flex bg-zinc-900/80 p-1 rounded-xl border border-zinc-800">
                {(['720p', '1080p'] as Resolution[]).map((res) => (
                  <button
                    key={res}
                    onClick={() => setResolution(res)}
                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
                      resolution === res ? 'bg-zinc-800 text-purple-400 shadow-inner' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    {res}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-3">
                <label className="text-sm text-zinc-400 font-medium uppercase tracking-wider">Motion Energy</label>
                <span className="text-xs font-bold text-purple-400 px-2 py-0.5 bg-purple-500/10 rounded border border-purple-500/20">{motion}%</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                value={motion}
                onChange={(e) => setMotion(parseInt(e.target.value))}
                className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <div className="flex justify-between mt-2 text-[10px] text-zinc-600 uppercase font-bold tracking-widest">
                <span>Static</span>
                <span>Hyper</span>
              </div>
            </div>

            <div className="pt-6 border-t border-zinc-800">
              <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-4">Live Diagnostics</h4>
              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">FPS Target</span>
                  <span className="text-zinc-100 font-mono">60.00</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">VRAM Usage</span>
                  <span className="text-zinc-100 font-mono">14.2 GB</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-400">Context Window</span>
                  <span className="text-zinc-100 font-mono">2048</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
