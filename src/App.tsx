import React, { useState } from 'react';
import { View, ActivityIndicator, useWindowDimensions } from 'react-native';
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
import { GameScreenLandscape } from './screens/GameScreenLandscape';
import { useGameState } from './hooks/useGameState';
import { Faction, ATMOSPHERES } from './theme';

export default function App() {
  const [fontsLoaded] = useFonts({
    Rajdhani_500Medium,
    Rajdhani_600SemiBold,
    Rajdhani_700Bold,
    ShareTechMono_400Regular,
  });

  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;

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

  const handleReset = () => {
    setScreen('setup');
    setCorpFaction(null);
    setRunnerFaction(null);
  };

  // Hook must be called unconditionally; uses fallback factions when on setup screen
  const game = useGameState({
    corpFaction: corpFaction ?? { id: '', name: 'CORP', short: 'C', color: theme.corp },
    runnerFaction: runnerFaction ?? { id: '', name: 'RUNNER', short: 'R', color: theme.runner },
    onReset: handleReset,
    theme,
  });

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

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <View style={{ flex: 1, backgroundColor: theme.bg }}>
        {screen === 'setup' ? (
          <SetupScreen onStart={handleStart} bg={theme.bg} />
        ) : isLandscape ? (
          <GameScreenLandscape game={game} />
        ) : (
          <GameScreen game={game} />
        )}
      </View>
    </SafeAreaProvider>
  );
}
