import React, { useEffect, useRef } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { rgba } from '../theme';
import { Mark } from '../state';

interface Props {
  mark: Mark | null;
  corpColor: string;
  onClear: () => void;
  /** User picks a central manually (no roll). */
  onOverride: (m: Mark) => void;
  /** Compact variant for landscape layout. */
  compact?: boolean;
}

const CYCLE: Mark[] = ['HQ', 'R&D', 'Archives'];

/** Mark indicator strip showing only the active central. Tap to cycle. Renders only when mark is set. */
export function MarkChip({ mark, corpColor, onClear, onOverride, compact = false }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: mark ? 1 : 0,
      duration: 180,
      useNativeDriver: false,
    }).start();
  }, [mark, opacity]);

  if (!mark) return null;

  const cycle = () => {
    const idx = CYCLE.indexOf(mark);
    const next = CYCLE[(idx + 1) % CYCLE.length];
    onOverride(next);
  };

  return (
    <Animated.View style={{ opacity }}>
      <View style={{
        alignSelf: 'flex-start',
        flexDirection: 'row', alignItems: 'center',
        paddingVertical: 2,
        paddingHorizontal: 6, gap: 5,
        backgroundColor: rgba(corpColor, 0.06),
        borderWidth: 1,
        borderColor: rgba(corpColor, 0.3),
        borderRadius: 10,
      }}>
        <View style={{
          width: 4, height: 4, borderRadius: 2,
          backgroundColor: corpColor,
        }} />
        <Text style={{
          fontSize: 8, letterSpacing: 1.2,
          color: rgba(corpColor, 0.6), fontFamily: 'Rajdhani_700Bold',
        }}>
          MARK
        </Text>

        <Pressable
          onPress={cycle}
          hitSlop={6}
          style={{
            flexDirection: 'row', alignItems: 'center', gap: 3,
            paddingVertical: 1, paddingHorizontal: 5,
            borderRadius: 6,
            backgroundColor: rgba(corpColor, 0.18),
          }}
        >
          <Text style={{
            fontSize: 10, letterSpacing: 0.5,
            color: corpColor, fontFamily: 'Rajdhani_700Bold',
          }}>
            {mark}
          </Text>
          <Text style={{
            fontSize: 8, color: rgba(corpColor, 0.6),
            fontFamily: 'Rajdhani_700Bold',
          }}>
            ↻
          </Text>
        </Pressable>

        <Pressable
          onPress={onClear}
          hitSlop={8}
          style={{ paddingHorizontal: 2 }}
        >
          <Text style={{
            fontSize: 10, color: rgba(corpColor, 0.5),
            fontFamily: 'Rajdhani_700Bold',
          }}>
            ✕
          </Text>
        </Pressable>
      </View>
    </Animated.View>
  );
}
