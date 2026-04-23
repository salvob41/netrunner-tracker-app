import React, { useEffect, useRef } from 'react';
import { View, Text, Pressable, Animated, StyleSheet } from 'react-native';
import { FactionGlyph } from './FactionGlyph';
import { Faction, C, rgba } from '../theme';

interface Props {
  winner: 'corp' | 'runner';
  corpFaction: Faction | null;
  runnerFaction: Faction | null;
  onReset: () => void;
}

export function WinOverlay({ winner, corpFaction, runnerFaction, onReset }: Props) {
  const isCorpWin = winner === 'corp';
  const faction = isCorpWin ? corpFaction : runnerFaction;
  const color = faction?.color || (isCorpWin ? '#2fb8ff' : '#ff5020');
  const label = isCorpWin
    ? (corpFaction?.name || 'CORPORATION')
    : (runnerFaction?.name || 'RUNNER');

  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.92)).current;

  // Fade + scale in on mount
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <Animated.View style={[StyleSheet.absoluteFillObject, {
      backgroundColor: 'rgba(7,9,13,0.92)',
      alignItems: 'center', justifyContent: 'center',
      opacity, zIndex: 100,
    }]}>
      <Animated.View style={{ alignItems: 'center', gap: 20, transform: [{ scale }] }}>
        <FactionGlyph faction={faction} size={72} />
        <View style={{ alignItems: 'center' }}>
          <Text style={{
            fontSize: 13, letterSpacing: 3, color: rgba(color, 0.7),
            fontFamily: 'Rajdhani_600SemiBold', marginBottom: 6,
          }}>
            {isCorpWin ? 'CORPORATION' : 'RUNNER'}
          </Text>
          <Text style={{
            fontSize: 36, fontWeight: '700', letterSpacing: 2, color,
            fontFamily: 'Rajdhani_700Bold',
          }}>
            {label.toUpperCase()}
          </Text>
          <Text style={{
            fontSize: 16, letterSpacing: 3, color: C.gold,
            fontFamily: 'Rajdhani_700Bold', marginTop: 4,
          }}>
            WINS
          </Text>
        </View>
        <Pressable
          onPressIn={onReset}
          style={{
            paddingVertical: 13, paddingHorizontal: 28, borderRadius: 8, marginTop: 16,
            backgroundColor: rgba(C.gold, 0.12),
            borderWidth: 1, borderColor: rgba(C.gold, 0.4),
          }}
        >
          <Text style={{ color: C.gold, fontFamily: 'Rajdhani_700Bold', fontSize: 13, letterSpacing: 2 }}>
            ⟳ NEW GAME
          </Text>
        </Pressable>
      </Animated.View>
    </Animated.View>
  );
}
