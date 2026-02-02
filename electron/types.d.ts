export interface ElectronAPI {
  secrets: {
    get: (key: string) => Promise<string | null>;
    set: (key: string, value: string) => Promise<boolean>;
    delete: (key: string) => Promise<boolean>;
    list: () => Promise<string[]>;
  };
  health: {
    check: () => Promise<Record<string, boolean>>;
    onStatus: (callback: (status: Record<string, boolean>) => void) => void;
  };
  oauth: {
    open: (provider: 'youtube' | 'instagram') => Promise<{ success: boolean; provider: string }>;
  };
}

declare global {
  interface Window {
    electron: ElectronAPI;
  }
}
