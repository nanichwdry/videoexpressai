
export type Resolution = '720p' | '1080p';

export interface VoicePreset {
  id: string;
  name: string;
  emotion: string;
}

export interface TrainingImage {
  id: string;
  url: string;
  file: File;
}

export enum DashboardTab {
  GENERATOR = 'generator',
  VOICE_LAB = 'voice_lab',
  ACTALKER = 'actalker',
  TRAINING = 'training',
  EXPORT = 'export'
}
