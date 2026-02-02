import { app, BrowserWindow, ipcMain, Tray, Menu, safeStorage } from 'electron';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';
import * as Sentry from '@sentry/electron/main';

Sentry.init({
  dsn: process.env.SENTRY_DSN || '',
  enabled: !!process.env.SENTRY_DSN,
});

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let backendProcess: ChildProcess | null = null;
let oauthWindow: BrowserWindow | null = null;

const BACKEND_PORT = 8000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const isDev = !app.isPackaged;

const SECRETS_PATH = path.join(app.getPath('userData'), 'secrets.enc');

function loadSecrets(): Record<string, string> {
  if (!fs.existsSync(SECRETS_PATH)) return {};
  try {
    const encrypted = fs.readFileSync(SECRETS_PATH);
    const decrypted = safeStorage.decryptString(encrypted);
    return JSON.parse(decrypted);
  } catch (e) {
    console.error('Failed to load secrets:', e);
    return {};
  }
}

function saveSecrets(secrets: Record<string, string>) {
  const json = JSON.stringify(secrets);
  const encrypted = safeStorage.encryptString(json);
  fs.writeFileSync(SECRETS_PATH, encrypted);
}

ipcMain.handle('secrets:get', async (_, key: string) => {
  const secrets = loadSecrets();
  return secrets[key] || null;
});

ipcMain.handle('secrets:set', async (_, key: string, value: string) => {
  const secrets = loadSecrets();
  secrets[key] = value;
  saveSecrets(secrets);
  return true;
});

ipcMain.handle('secrets:delete', async (_, key: string) => {
  const secrets = loadSecrets();
  delete secrets[key];
  saveSecrets(secrets);
  return true;
});

ipcMain.handle('secrets:list', async () => {
  const secrets = loadSecrets();
  return Object.keys(secrets);
});

async function startBackend(): Promise<boolean> {
  return new Promise((resolve) => {
    const backendDir = isDev
      ? path.join(__dirname, '..', 'backend')
      : path.join(process.resourcesPath, 'backend');

    const pythonExe = isDev ? 'python' : path.join(process.resourcesPath, 'backend', 'python', 'python.exe');
    const mainPy = path.join(backendDir, 'main.py');

    console.log('[Backend] Starting:', pythonExe, mainPy);

    backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
      cwd: backendDir,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    backendProcess.stdout?.on('data', (data) => {
      console.log('[Backend]', data.toString());
    });

    backendProcess.stderr?.on('data', (data) => {
      console.error('[Backend Error]', data.toString());
    });

    backendProcess.on('error', (err) => {
      console.error('[Backend] Failed to start:', err);
      Sentry.captureException(err);
      resolve(false);
    });

    let attempts = 0;
    const checkHealth = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        if (res.ok) {
          clearInterval(checkHealth);
          console.log('[Backend] Ready');
          resolve(true);
        }
      } catch (e) {
        attempts++;
        if (attempts > 30) {
          clearInterval(checkHealth);
          console.error('[Backend] Failed to start after 30s');
          resolve(false);
        }
      }
    }, 1000);
  });
}

async function performHealthChecks(): Promise<Record<string, boolean>> {
  const results: Record<string, boolean> = {
    backend: false,
    runpod: false,
    supabase: false,
    r2: false,
  };

  try {
    const res = await fetch(`${BACKEND_URL}/health`, { signal: AbortSignal.timeout(5000) });
    if (res.ok) {
      const data = await res.json();
      results.backend = true;
      results.runpod = data.runpod_connected || false;
    }
  } catch (e) {
    console.error('[Health] Backend check failed:', e);
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  if (supabaseUrl) {
    try {
      const res = await fetch(`${supabaseUrl}/rest/v1/`, {
        headers: { apikey: process.env.SUPABASE_ANON_KEY || '' },
        signal: AbortSignal.timeout(5000),
      });
      results.supabase = res.ok;
    } catch (e) {
      console.error('[Health] Supabase check failed:', e);
    }
  }

  const r2PublicUrl = process.env.R2_PUBLIC_BASE_URL;
  if (r2PublicUrl) {
    try {
      const res = await fetch(r2PublicUrl, { method: 'HEAD', signal: AbortSignal.timeout(5000) });
      results.r2 = res.ok || res.status === 403;
    } catch (e) {
      console.error('[Health] R2 check failed:', e);
    }
  }

  return results;
}

ipcMain.handle('health:check', async () => {
  return await performHealthChecks();
});

ipcMain.handle('oauth:open', async (_, provider: 'youtube' | 'instagram') => {
  return new Promise((resolve, reject) => {
    const authUrls = {
      youtube: `https://accounts.google.com/o/oauth2/v2/auth?client_id=${process.env.GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent('http://localhost:8000/oauth/youtube/callback')}&response_type=code&scope=${encodeURIComponent('https://www.googleapis.com/auth/youtube.upload')}`,
      instagram: `https://api.instagram.com/oauth/authorize?client_id=${process.env.INSTAGRAM_CLIENT_ID}&redirect_uri=${encodeURIComponent('http://localhost:8000/oauth/instagram/callback')}&scope=user_profile,user_media&response_type=code`,
    };

    oauthWindow = new BrowserWindow({
      width: 600,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
      },
    });

    oauthWindow.loadURL(authUrls[provider]);

    oauthWindow.webContents.on('will-redirect', async (event, url) => {
      if (url.startsWith('http://localhost:8000/oauth/')) {
        event.preventDefault();
        
        const urlObj = new URL(url);
        const code = urlObj.searchParams.get('code');
        const error = urlObj.searchParams.get('error');

        if (error) {
          reject(new Error(error));
          oauthWindow?.close();
          return;
        }

        if (code) {
          try {
            const res = await fetch(`${BACKEND_URL}/oauth/${provider}/callback`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code }),
            });

            if (res.ok) {
              const data = await res.json();
              resolve(data);
            } else {
              reject(new Error('Token exchange failed'));
            }
          } catch (e) {
            reject(e);
          }
          oauthWindow?.close();
        }
      }
    });

    oauthWindow.on('closed', () => {
      oauthWindow = null;
      reject(new Error('OAuth window closed'));
    });
  });
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  tray = new Tray(path.join(__dirname, '..', 'assets', 'tray-icon.png'));

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show App',
      click: () => {
        mainWindow?.show();
      },
    },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('VideoExpress AI');
  tray.setContextMenu(contextMenu);

  tray.on('click', () => {
    mainWindow?.show();
  });
}

app.whenReady().then(async () => {
  console.log('[App] Starting...');

  const backendStarted = await startBackend();
  if (!backendStarted) {
    console.error('[App] Backend failed to start');
    Sentry.captureMessage('Backend failed to start', 'error');
  }

  const health = await performHealthChecks();
  console.log('[App] Health checks:', health);

  createWindow();
  createTray();

  mainWindow?.webContents.on('did-finish-load', () => {
    mainWindow?.webContents.send('health:status', health);
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    // Keep running in tray
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  } else {
    mainWindow.show();
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
  
  if (backendProcess) {
    backendProcess.kill();
  }
});

process.on('uncaughtException', (error) => {
  console.error('[Uncaught Exception]', error);
  Sentry.captureException(error);
});

process.on('unhandledRejection', (reason) => {
  console.error('[Unhandled Rejection]', reason);
  Sentry.captureException(reason);
});
