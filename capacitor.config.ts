import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.manutencaopro.app',
  appName: 'ManutencaoPro',
  webDir: 'dist',
  server: {
    url: 'https://48f98657-ad81-4d13-abe1-4f5ef5216527.lovableproject.com?forceHideBadge=true',
    cleartext: true
  }
};

export default config;
