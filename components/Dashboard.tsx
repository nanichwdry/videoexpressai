
import React from 'react';
import { DashboardTab } from '../types';
import { WanControlPanel } from './WanControlPanel';
import { VoiceLab } from './VoiceLab';
import { ACTalker } from './ACTalker';
import { TrainingStudio } from './TrainingStudio';
import { SocialHub } from './SocialHub';

interface DashboardProps {
  activeTab: DashboardTab;
}

export const Dashboard: React.FC<DashboardProps> = ({ activeTab }) => {
  return (
    <div className="w-full">
      {activeTab === DashboardTab.GENERATOR && <WanControlPanel />}
      {activeTab === DashboardTab.VOICE_LAB && <VoiceLab />}
      {activeTab === DashboardTab.ACTALKER && <ACTalker />}
      {activeTab === DashboardTab.TRAINING && <TrainingStudio />}
      {activeTab === DashboardTab.EXPORT && <SocialHub />}
    </div>
  );
};
