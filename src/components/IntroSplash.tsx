import { useEffect, useRef } from 'react';
import { StyleSheet, Pressable, Animated } from 'react-native';
import { Image } from 'expo-image';
import * as SplashScreen from 'expo-splash-screen';

const FOX = require('../assets/fox.webp');

interface Props {
  onDone: () => void;
}

/**
 * Animated intro: the fox animation (transparent WebP, white background flood-
 * filled out) plays over a dark background, then hands off to the main app.
 * No white anywhere — the old fox.mp4 had a white background baked in.
 *
 * Cold-start handoff:
 *   1. Native splash shows the fox on a dark background (expo-splash-screen)
 *   2. RN bundle loads, App.tsx renders this component
 *   3. useEffect fires SplashScreen.hideAsync() and the WebP plays (~2.4s)
 *   4. After the animation, onDone() transitions to the setup screen
 *
 * Skippable via tap.
 */
export function IntroSplash({ onDone }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});

    Animated.timing(opacity, { toValue: 1, duration: 350, useNativeDriver: true }).start();

    // Animation runs ~2.4s; transition just after it completes.
    const timer = setTimeout(onDone, 2600);
    return () => clearTimeout(timer);
  }, [onDone, opacity]);

  return (
    <Pressable style={styles.container} onPress={onDone}>
      <Animated.View style={{ opacity }}>
        <Image source={FOX} style={styles.fox} contentFit="contain" />
      </Animated.View>
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
  fox: {
    width: 220,
    height: 220,
  },
});
