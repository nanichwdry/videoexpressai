import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', {
  secrets: {
    get: (key: string) => ipcRenderer.invoke('secrets:get', key),
    set: (key: string, value: string) => ipcRenderer.invoke('secrets:set', key, value),
    delete: (key: string) => ipcRenderer.invoke('secrets:delete', key),
    list: () => ipcRenderer.invoke('secrets:list'),
  },
  health: {
    check: () => ipcRenderer.invoke('health:check'),
    onStatus: (callback: (status: Record<string, boolean>) => void) => {
      ipcRenderer.on('health:status', (_, status) => callback(status));
    },
  },
  oauth: {
    open: (provider: 'youtube' | 'instagram') => ipcRenderer.invoke('oauth:open', provider),
  },
});
