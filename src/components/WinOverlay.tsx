import React, { useState, useEffect, useRef } from 'react';
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
  const [hidden, setHidden] = useState(false);
  const isCorpWin = winner === 'corp';
  const faction = isCorpWin ? corpFaction : runnerFaction;
  const color = faction?.color || (isCorpWin ? '#2fb8ff' : '#ff5020');
  const label = isCorpWin
    ? (corpFaction?.name || 'CORPORATION')
    : (runnerFaction?.name || 'RUNNER');

  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.92)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 300, useNativeDriver: true }),
    ]).start();
  }, []);

  // Peek mode: show a small floating banner to restore the overlay
  if (hidden) {
    return (
      <Pressable
        onPressIn={() => setHidden(false)}
        style={{
          position: 'absolute', bottom: 80, alignSelf: 'center',
          flexDirection: 'row', alignItems: 'center', gap: 8,
          backgroundColor: rgba(color, 0.18),
          borderWidth: 1, borderColor: rgba(color, 0.5),
          borderRadius: 20, paddingVertical: 8, paddingHorizontal: 16,
          zIndex: 100,
        }}
      >
        <Text style={{ fontSize: 11, color, fontFamily: 'Rajdhani_700Bold', letterSpacing: 1.5 }}>
          {label.toUpperCase()} WINS
        </Text>
        <Text style={{ fontSize: 10, color: rgba(color, 0.6), fontFamily: 'Rajdhani_600SemiBold', letterSpacing: 1 }}>
          TAP TO RESTORE
        </Text>
      </Pressable>
    );
  }

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
        <Pressable
          onPressIn={() => setHidden(true)}
          style={{ paddingVertical: 6, paddingHorizontal: 12 }}
        >
          <Text style={{
            fontSize: 10, color: rgba(C.dim, 0.6),
            fontFamily: 'Rajdhani_600SemiBold', letterSpacing: 1.5,
          }}>
            VIEW FINAL BOARD
          </Text>
        </Pressable>
      </Animated.View>
    </Animated.View>
  );
}
