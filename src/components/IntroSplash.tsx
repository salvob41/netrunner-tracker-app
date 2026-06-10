import { useEffect, useRef } from 'react';
import { StyleSheet, Pressable, Animated } from 'react-native';
import * as SplashScreen from 'expo-splash-screen';

const FOX = require('../assets/adaptive-icon.png');

interface Props {
  onDone: () => void;
}

/**
 * Animated intro: the transparent fox fades and scales in over a dark
 * background, then hands off to the main app. No video (the old fox.mp4 had a
 * white background baked in), so there's nothing white to flash.
 *
 * Cold-start handoff:
 *   1. Native splash shows the fox on a dark background (expo-splash-screen)
 *   2. RN bundle loads, App.tsx renders this component
 *   3. useEffect fires SplashScreen.hideAsync() and starts the animation
 *   4. After ~1.6s onDone() transitions to the setup screen
 *
 * Skippable via tap.
 */
export function IntroSplash({ onDone }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.85)).current;

  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});

    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 450, useNativeDriver: true }),
      Animated.spring(scale, { toValue: 1, friction: 6, tension: 40, useNativeDriver: true }),
    ]).start();

    const timer = setTimeout(onDone, 1600);
    return () => clearTimeout(timer);
  }, [onDone, opacity, scale]);

  return (
    <Pressable style={styles.container} onPress={onDone}>
      <Animated.Image
        source={FOX}
        style={[styles.fox, { opacity, transform: [{ scale }] }]}
        resizeMode="contain"
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
  fox: {
    width: 200,
    height: 200,
  },
});
