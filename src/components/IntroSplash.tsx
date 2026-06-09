import { useEffect } from 'react';
import { View, StyleSheet, Pressable } from 'react-native';
import { VideoView, useVideoPlayer } from 'expo-video';
import * as SplashScreen from 'expo-splash-screen';

const FOX_VIDEO = require('../assets/fox.mp4');

interface Props {
  onDone: () => void;
}

/**
 * Plays the fox animation once over the native splash background,
 * then hands off to the main app.
 *
 * Cold-start handoff:
 *   1. Native splash shows fox icon (static) from app.json `splash`
 *   2. RN bundle loads, App.tsx renders this component
 *   3. useEffect fires SplashScreen.hideAsync() to reveal video
 *   4. Video plays for ~2.4s
 *   5. Timeout fires onDone(), App transitions to setup screen
 *
 * Skippable via tap (escape hatch for impatient users).
 */
export function IntroSplash({ onDone }: Props) {
  const player = useVideoPlayer(FOX_VIDEO, (p) => {
    p.loop = false;
    p.muted = true;
    p.play();
  });

  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});

    // Safety timeout slightly longer than video duration (2.4s)
    const timer = setTimeout(onDone, 2700);
    return () => clearTimeout(timer);
  }, [onDone]);

  return (
    <Pressable style={styles.container} onPress={onDone}>
      <VideoView
        player={player}
        style={styles.video}
        contentFit="contain"
        nativeControls={false}
      />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#07090d',
    alignItems: 'center',
    justifyContent: 'center',
  },
  video: {
    width: 320,
    height: 320,
  },
});
