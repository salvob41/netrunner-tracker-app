import React, { useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import {
  useFonts,
  Rajdhani_500Medium,
  Rajdhani_600SemiBold,
  Rajdhani_700Bold,
} from '@expo-google-fonts/rajdhani';
import { ShareTechMono_400Regular } from '@expo-google-fonts/share-tech-mono';
import { StatusBar } from 'expo-status-bar';
import { SetupScreen } from './screens/SetupScreen';
import { GameScreen } from './screens/GameScreen';
import { Faction, ATMOSPHERES } from './theme';

export default function App() {
  const [fontsLoaded] = useFonts({
    Rajdhani_500Medium,
    Rajdhani_600SemiBold,
    Rajdhani_700Bold,
    ShareTechMono_400Regular,
  });

  const [screen, setScreen] = useState<'setup' | 'game'>('setup');
  const [corpFaction, setCorpFaction] = useState<Faction | null>(null);
  const [runnerFaction, setRunnerFaction] = useState<Faction | null>(null);

  // Default to Neon Punk theme; easily swappable in the future
  const atm = ATMOSPHERES['Neon Punk'];
  const theme = {
    ...atm,
    tokenRadius: 12,
    inactiveOpacity: 0.72,
  };

  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, backgroundColor: '#07090d', alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color="#2fb8ff" />
      </View>
    );
  }

  const handleStart = (corp: Faction, runner: Faction) => {
    setCorpFaction(corp);
    setRunnerFaction(runner);
    setScreen('game');
  };

  const handleReset = () => {
    setScreen('setup');
    setCorpFaction(null);
    setRunnerFaction(null);
  };

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <View style={{ flex: 1, backgroundColor: theme.bg }}>
        {screen === 'setup' ? (
          <SetupScreen onStart={handleStart} bg={theme.bg} />
        ) : (
          <GameScreen
            corpFaction={corpFaction!}
            runnerFaction={runnerFaction!}
            onReset={handleReset}
            theme={theme}
          />
        )}
      </View>
    </SafeAreaProvider>
  );
}
