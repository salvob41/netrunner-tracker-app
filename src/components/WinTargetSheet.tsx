import React, { useEffect, useRef, useState } from 'react';
import { View, Text, Pressable, Animated, StyleSheet } from 'react-native';
import { C, rgba } from '../theme';
import { MIN_WIN_TARGET, MAX_WIN_TARGET } from '../state';

interface Props {
  /** Current agenda-to-win target. */
  value: number;
  /** Commit a new absolute target. */
  onSet: (value: number) => void;
  onClose: () => void;
}

const PRESETS = [5, 6, 7];

export function WinTargetSheet({ value, onSet, onClose }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.92)).current;
  const [target, setTarget] = useState(value);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 180, useNativeDriver: false }),
      Animated.spring(scale, { toValue: 1, friction: 7, tension: 110, useNativeDriver: false }),
    ]).start();
  }, []);

  const close = (commit: boolean) => {
    if (commit) onSet(target);
    Animated.parallel([
      Animated.timing(opacity, { toValue: 0, duration: 150, useNativeDriver: false }),
      Animated.timing(scale, { toValue: 0.92, duration: 150, useNativeDriver: false }),
    ]).start(onClose);
  };

  const step = (d: number) =>
    setTarget(n => Math.max(MIN_WIN_TARGET, Math.min(MAX_WIN_TARGET, n + d)));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, {
      backgroundColor: 'rgba(7,9,13,0.85)',
      opacity, justifyContent: 'center', alignItems: 'center',
      padding: 20, zIndex: 60, elevation: 60,
    }]}>
      <Pressable style={StyleSheet.absoluteFill} onPress={() => close(false)} />
      <Animated.View style={{
        width: '100%', maxWidth: 340,
        backgroundColor: '#0d1119',
        borderRadius: 16, borderWidth: 1, borderColor: '#1a2535',
        transform: [{ scale }], paddingBottom: 16, overflow: 'hidden',
      }}>
        {/* Header */}
        <View style={{
          flexDirection: 'row', alignItems: 'center',
          padding: 12, paddingHorizontal: 16,
          borderBottomWidth: 1, borderBottomColor: '#1a2535',
        }}>
          <Text style={{
            fontSize: 10, letterSpacing: 2, fontWeight: '700',
            color: C.dim, fontFamily: 'Rajdhani_700Bold', flex: 1,
          }}>
            AGENDA TO WIN
          </Text>
          <Pressable onPress={() => close(false)} style={{ padding: 4, paddingHorizontal: 8 }}>
            <Text style={{ fontSize: 14, color: C.dim }}>✕</Text>
          </Pressable>
        </View>

        {/* Stepper */}
        <View style={{
          flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
          gap: 20, paddingVertical: 22,
        }}>
          <StepBtn label="−" onPress={() => step(-1)} />
          <View style={{ alignItems: 'center', minWidth: 64 }}>
            <Text style={{
              fontSize: 56, color: C.gold, lineHeight: 60,
              fontFamily: 'ShareTechMono_400Regular',
            }}>
              {target}
            </Text>
          </View>
          <StepBtn label="+" onPress={() => step(1)} />
        </View>

        {/* Presets */}
        <View style={{ flexDirection: 'row', gap: 8, paddingHorizontal: 16 }}>
          {PRESETS.map(n => {
            const active = target === n;
            return (
              <Pressable
                key={n}
                onPressIn={() => setTarget(n)}
                style={{
                  flex: 1, paddingVertical: 11, borderRadius: 10,
                  borderWidth: 1.5,
                  borderColor: rgba(C.gold, active ? 0.7 : 0.25),
                  backgroundColor: rgba(C.gold, active ? 0.18 : 0.06),
                  alignItems: 'center',
                }}
              >
                <Text style={{
                  fontSize: 16, letterSpacing: 1,
                  color: C.gold, fontFamily: 'Rajdhani_700Bold',
                }}>
                  {n}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* Done */}
        <View style={{ paddingHorizontal: 16, paddingTop: 12 }}>
          <Pressable
            onPressIn={() => close(true)}
            style={{
              paddingVertical: 14, borderRadius: 10,
              borderWidth: 1.5, borderColor: rgba('#00f0a0', 0.45),
              backgroundColor: rgba('#00f0a0', 0.12),
              alignItems: 'center',
            }}
          >
            <Text style={{
              fontSize: 14, letterSpacing: 2,
              color: '#00f0a0', fontFamily: 'Rajdhani_700Bold',
            }}>
              SET TO {target}
            </Text>
          </Pressable>
        </View>
      </Animated.View>
    </Animated.View>
  );
}

function StepBtn({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable
      onPressIn={onPress}
      hitSlop={8}
      style={{
        width: 48, height: 48, borderRadius: 12,
        borderWidth: 1.5, borderColor: rgba(C.gold, 0.35),
        backgroundColor: rgba(C.gold, 0.10),
        alignItems: 'center', justifyContent: 'center',
      }}
    >
      <Text style={{ fontSize: 28, lineHeight: 30, color: C.gold, fontFamily: 'Rajdhani_700Bold' }}>
        {label}
      </Text>
    </Pressable>
  );
}
