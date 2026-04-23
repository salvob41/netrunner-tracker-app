import React, { useEffect, useRef } from 'react';
import { View, Text, Pressable, Animated, ScrollView, StyleSheet } from 'react-native';
import { LogEntry } from '../state';
import { C, rgba } from '../theme';

interface Props {
  log: LogEntry[];
  onClose: () => void;
}

function LogRow({ entry }: { entry: LogEntry }) {
  const colors: Record<string, string> = {
    corp: '#2fb8ff',
    runner: '#ff5020',
    game: C.gold,
  };
  const color = colors[entry.player] || C.dim;
  return (
    <View style={{
      flexDirection: 'row', gap: 8, alignItems: 'center',
      paddingVertical: 7, paddingHorizontal: 12,
      borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.05)',
    }}>
      <Text style={{
        fontSize: 9, color: rgba(color, 0.6),
        fontFamily: 'Rajdhani_600SemiBold', minWidth: 56, letterSpacing: 0.5,
      }}>
        R{entry.round}·{entry.player.toUpperCase()}
      </Text>
      <Text style={{ fontSize: 11, color: C.text, flex: 1, fontFamily: 'Rajdhani_500Medium' }}>
        {entry.message}
      </Text>
    </View>
  );
}

export function LogSheet({ log, onClose }: Props) {
  const translateY = useRef(new Animated.Value(400)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  // Slide up on mount
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 200, useNativeDriver: true }),
      Animated.timing(translateY, { toValue: 0, duration: 250, useNativeDriver: true }),
    ]).start();
  }, []);

  const close = () => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 0, duration: 180, useNativeDriver: true }),
      Animated.timing(translateY, { toValue: 400, duration: 200, useNativeDriver: true }),
    ]).start(onClose);
  };

  return (
    <Animated.View style={[StyleSheet.absoluteFillObject, {
      backgroundColor: 'rgba(7,9,13,0.85)',
      opacity,
      justifyContent: 'flex-end',
      zIndex: 50,
    }]}>
      {/* Backdrop tap to dismiss */}
      <Pressable style={StyleSheet.absoluteFillObject} onPress={close} />
      <Animated.View style={{
        backgroundColor: '#0d1119',
        borderRadius: 16, borderBottomLeftRadius: 0, borderBottomRightRadius: 0,
        borderWidth: 1, borderColor: '#1a2535', maxHeight: '65%',
        transform: [{ translateY }],
      }}>
        <View style={{
          flexDirection: 'row', alignItems: 'center',
          padding: 12, paddingHorizontal: 16,
          borderBottomWidth: 1, borderBottomColor: '#1a2535',
        }}>
          <Text style={{
            fontSize: 10, letterSpacing: 2, fontWeight: '700',
            color: C.dim, fontFamily: 'Rajdhani_700Bold', flex: 1,
          }}>
            GAME LOG
          </Text>
          <Text style={{ fontSize: 9, color: C.gold, fontFamily: 'Rajdhani_600SemiBold' }}>
            {log.length} events
          </Text>
          <Pressable onPress={close} style={{ padding: 4, paddingHorizontal: 8, marginLeft: 8 }}>
            <Text style={{ fontSize: 14, color: C.dim }}>✕</Text>
          </Pressable>
        </View>
        <ScrollView>
          {[...log].reverse().map((e, i) => <LogRow key={i} entry={e} />)}
          {log.length === 0 && (
            <Text style={{
              padding: 20, color: C.dim, textAlign: 'center',
              fontFamily: 'Rajdhani_500Medium', fontSize: 12,
            }}>
              No events yet
            </Text>
          )}
        </ScrollView>
      </Animated.View>
    </Animated.View>
  );
}
