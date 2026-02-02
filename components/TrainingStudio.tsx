
import React, { useState } from 'react';
import { TrainingImage } from '../types';

export const TrainingStudio: React.FC = () => {
  const [images, setImages] = useState<TrainingImage[]>([]);
  const [trainingName, setTrainingName] = useState('');
  const [training, setTraining] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // FIX: Explicitly cast files to File[] to resolve 'unknown' type inference and allow URL.createObjectURL
    const files = Array.from(e.target.files || []) as File[];
    const newImages: TrainingImage[] = files.map(file => ({
      id: Math.random().toString(36).substring(2, 11),
      url: URL.createObjectURL(file),
      file
    }));
    setImages(prev => [...prev, ...newImages]);
  };

  const removeImage = (id: string) => {
    setImages(prev => prev.filter(img => img.id !== id));
  };

  const startTraining = () => {
    setTraining(true);
    setTimeout(() => setTraining(false), 10000);
  };

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <div className="obsidian-glass rounded-2xl p-6 border border-purple-500/10">
            <h3 className="text-lg font-bold mb-4">Project Parameters</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest block mb-2">Subject Identity</label>
                <input 
                  type="text" 
                  value={trainingName}
                  onChange={(e) => setTrainingName(e.target.value)}
                  placeholder="e.g. DigitalTwin_Alpha"
                  className="w-full bg-zinc-900/80 border border-zinc-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-purple-500/50"
                />
              </div>
              <div className="p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
                <p className="text-xs text-zinc-500 mb-2">Training Steps</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-zinc-200">2,500 Iterations</span>
                  <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">Optimal</span>
                </div>
              </div>
              <button
                onClick={startTraining}
                disabled={training || images.length < 15}
                className={`w-full py-4 rounded-xl font-bold transition-all ${
                  training || images.length < 15 
                    ? 'bg-zinc-800 text-zinc-600 cursor-not-allowed border border-zinc-700' 
                    : 'bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]'
                }`}
              >
                {training ? 'Training Digital Twin...' : 'Launch LoRA Pipeline'}
              </button>
              {images.length < 15 && (
                <p className="text-[10px] text-zinc-500 text-center uppercase tracking-widest font-bold">
                  {15 - images.length} more images required
                </p>
              )}
            </div>
          </div>

          <div className="obsidian-glass rounded-2xl p-6 bg-zinc-950">
             <h4 className="text-xs font-bold text-zinc-400 uppercase mb-4 tracking-tighter">AI-Toolkit 4.0 Suite</h4>
             <ul className="space-y-2">
               {['Cross-Attention Control', 'U-Net Gradient Refinement', 'FaceID V2 Alignment', 'Noise Offset Calibration'].map(feat => (
                 <li key={feat} className="flex items-center gap-2 text-xs text-zinc-500">
                   <svg className="w-3 h-3 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                   </svg>
                   {feat}
                 </li>
               ))}
             </ul>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="obsidian-glass rounded-2xl p-6 h-full border border-zinc-800 flex flex-col">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold">Training Set <span className="text-zinc-500 font-medium">({images.length}/30)</span></h3>
              <label className="cursor-pointer px-4 py-2 bg-purple-600/10 hover:bg-purple-600/20 text-purple-400 border border-purple-500/30 rounded-lg transition-all text-sm font-bold">
                 Add Photos
                 <input type="file" multiple className="hidden" accept="image/*" onChange={handleFileChange} />
              </label>
            </div>

            {training ? (
              <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
                <div className="w-full max-w-md bg-zinc-900 rounded-full h-2 mb-8 overflow-hidden relative">
                   <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-fuchsia-500 to-purple-600 animate-[shimmer_2s_infinite] w-[400%]"></div>
                </div>
                <h4 className="text-2xl font-bold text-zinc-100 mb-2">Refining Weight Tensors</h4>
                <p className="text-zinc-500 italic">Loss: 0.0423 | LR: 0.0001 | ETA: 4m 12s</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4 overflow-y-auto max-h-[600px] pr-2 custom-scrollbar">
                {images.map(img => (
                  <div key={img.id} className="relative aspect-square group rounded-xl overflow-hidden bg-zinc-900 border border-zinc-800">
                    <img src={img.url} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" alt="Training" />
                    <button 
                      onClick={() => removeImage(img.id)}
                      className="absolute top-2 right-2 w-8 h-8 bg-black/60 backdrop-blur-md rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                    <div className="absolute inset-0 border-2 border-transparent group-hover:border-purple-500/50 rounded-xl pointer-events-none"></div>
                  </div>
                ))}
                {images.length === 0 && (
                  <div className="col-span-full h-64 flex flex-col items-center justify-center text-zinc-600 space-y-4">
                    <svg className="w-16 h-16 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p className="font-medium">No training assets detected</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
