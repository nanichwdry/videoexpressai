import type { ForgeConfig } from '@electron-forge/shared-types';
import { MakerSquirrel } from '@electron-forge/maker-squirrel';
import { MakerDMG } from '@electron-forge/maker-dmg';
import { WebpackPlugin } from '@electron-forge/plugin-webpack';
import { mainConfig } from './webpack.main.config';
import { rendererConfig } from './webpack.renderer.config';

const config: ForgeConfig = {
  packagerConfig: {
    name: 'VideoExpress AI',
    executableName: 'videoexpress',
    icon: './assets/icon',
    asar: true,
    extraResource: [
      './backend',
    ],
    osxSign: {
      identity: process.env.APPLE_IDENTITY,
      'hardened-runtime': true,
      entitlements: 'entitlements.plist',
      'entitlements-inherit': 'entitlements.plist',
      'signature-flags': 'library',
    },
    osxNotarize: {
      tool: 'notarytool',
      appleId: process.env.APPLE_ID!,
      appleIdPassword: process.env.APPLE_PASSWORD!,
      teamId: process.env.APPLE_TEAM_ID!,
    },
  },
  rebuildConfig: {},
  makers: [
    new MakerSquirrel({
      name: 'VideoExpressAI',
      authors: 'VideoExpress',
      description: 'AI-powered video creation platform',
      setupIcon: './assets/icon.ico',
      loadingGif: './assets/install.gif',
      certificateFile: process.env.WINDOWS_CERT_FILE,
      certificatePassword: process.env.WINDOWS_CERT_PASSWORD,
    }),
    new MakerDMG({
      name: 'VideoExpress AI',
      icon: './assets/icon.icns',
      background: './assets/dmg-background.png',
      format: 'ULFO',
    }),
  ],
  plugins: [
    new WebpackPlugin({
      mainConfig,
      renderer: {
        config: rendererConfig,
        entryPoints: [
          {
            html: './src/index.html',
            js: './src/renderer.ts',
            name: 'main_window',
            preload: {
              js: './electron/preload.ts',
            },
          },
        ],
      },
    }),
  ],
};

export default config;
