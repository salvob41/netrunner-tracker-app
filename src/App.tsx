import React, { useState, useEffect } from 'react';
import { View, ActivityIndicator, useWindowDimensions, BackHandler, Alert } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import {
  useFonts,
  Rajdhani_500Medium,
  Rajdhani_600SemiBold,
  Rajdhani_700Bold,
} from '@expo-google-fonts/rajdhani';
import { ShareTechMono_400Regular } from '@expo-google-fonts/share-tech-mono';
import { StatusBar } from 'expo-status-bar';
import { useKeepAwake } from 'expo-keep-awake';
import * as SplashScreen from 'expo-splash-screen';
import { SetupScreen } from './screens/SetupScreen';
import { GameScreen } from './screens/GameScreen';
import { GameScreenLandscape } from './screens/GameScreenLandscape';
import { IntroSplash } from './components/IntroSplash';
import { useGameState } from './hooks/useGameState';
import { Faction, PlayMode, ATMOSPHERES } from './theme';

// Keep the native splash visible until IntroSplash takes over.
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function App() {
  useKeepAwake();
  const [introDone, setIntroDone] = useState(false);
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
  const [mode, setMode] = useState<PlayMode>('both');

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
    setMode('both');
  };

  // Hook must be called unconditionally; uses fallback factions when on setup screen
  const game = useGameState({
    corpFaction: corpFaction ?? { id: '', name: 'CORP', short: 'C', color: theme.corp },
    runnerFaction: runnerFaction ?? { id: '', name: 'RUNNER', short: 'R', color: theme.runner },
    onReset: handleReset,
    theme,
  });

  // Intercept the Android hardware back button so it never silently kills the
  // app. On the game screen a back press offers to return to setup or quit; on
  // the setup screen it just confirms the quit.
  useEffect(() => {
    const onBack = () => {
      if (screen === 'game') {
        Alert.alert(
          'Leave game?',
          'Your current game will be lost.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Back to Setup', onPress: handleReset },
            { text: 'Quit', style: 'destructive', onPress: () => BackHandler.exitApp() },
          ],
          { cancelable: true },
        );
      } else {
        Alert.alert(
          'Quit Trackster Taka?',
          '',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Quit', style: 'destructive', onPress: () => BackHandler.exitApp() },
          ],
          { cancelable: true },
        );
      }
      return true; // prevent the default exit
    };
    const sub = BackHandler.addEventListener('hardwareBackPress', onBack);
    return () => sub.remove();
  }, [screen]);

  if (!introDone) {
    return <IntroSplash onDone={() => setIntroDone(true)} />;
  }

  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, backgroundColor: '#07090d', alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color="#2fb8ff" />
      </View>
    );
  }

  const handleStart = (corp: Faction, runner: Faction, m: PlayMode) => {
    setCorpFaction(corp);
    setRunnerFaction(runner);
    setMode(m);
    // Flip the corp panel only in two-player (BOTH) mode, where players sit
    // face-to-face. In solo CORP/RUNNER mode one person faces the screen
    // normally, so corp must not be upside down. (Manual ⇅ toggle still works.)
    game.setCorpFlipped(m === 'both');
    game.setRunnerFlipped(false);
    setScreen('game');
  };

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <View style={{ flex: 1, backgroundColor: theme.bg }}>
        {screen === 'setup' ? (
          <SetupScreen onStart={handleStart} bg={theme.bg} />
        ) : isLandscape ? (
          <GameScreenLandscape game={game} mode={mode} />
        ) : (
          <GameScreen game={game} mode={mode} />
        )}
      </View>
    </SafeAreaProvider>
  );
}
