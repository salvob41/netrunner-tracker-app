import React, { useRef } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { Icon } from './Icon';
import { rgba } from '../theme';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

const CREDIT_ICON = require('../assets/credit.png');

const PILL_GREEN = '#00f0a0';
const PILL_RED   = '#ff2040';

interface Props {
  value: number;
  color: string;
  onChange: (delta: number) => void;
  label?: string;
  flushRef?: React.MutableRefObject<() => void>;
}

export function CreditCounter({ value, color, onChange, label, flushRef }: Props) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const { pending, bump, flush } = useBatchedDelta(onChange);

  // Keep flushRef current (safe ref assignment during render).
  if (flushRef) flushRef.current = flush;

  const displayValue = value + pending;

  const tap = (delta: number) => {
    bump(delta);
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 1.22, duration: 80, useNativeDriver: false }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 140, useNativeDriver: false }),
    ]).start();
  };

  const pillColor = pending >= 0 ? PILL_GREEN : PILL_RED;
  const pillLabel = pending > 0 ? `+${pending}` : `\u2212${Math.abs(pending)}`;

  return (
    <View style={{
      flex: 1, borderRadius: 14, overflow: 'hidden',
      backgroundColor: rgba(color, 0.07),
      borderWidth: 2, borderColor: rgba(color, 0.25),
    }}>
      {/* Left half: decrement tap zone */}
      <Pressable
        onPressIn={() => tap(-1)}
        style={{
          position: 'absolute', left: 0, top: 0, bottom: 0, width: '50%',
          justifyContent: 'center', paddingLeft: 22,
        }}
      >
        <Text style={{ color: rgba(color, 0.45), fontSize: 40, fontWeight: '200', lineHeight: 44 }}>−</Text>
      </Pressable>
      {/* Right half: increment tap zone */}
      <Pressable
        onPressIn={() => tap(+1)}
        style={{
          position: 'absolute', right: 0, top: 0, bottom: 0, width: '50%',
          alignItems: 'flex-end', justifyContent: 'center', paddingRight: 22,
        }}
      >
        <Text style={{ color: rgba(color, 0.45), fontSize: 40, fontWeight: '200', lineHeight: 44 }}>+</Text>
      </Pressable>
      {/* Center display — pointerEvents none so taps pass through to ± zones */}
      <View
        style={{
          position: 'absolute', top: 0, bottom: 0, left: 0, right: 0,
          alignItems: 'center', justifyContent: 'center', gap: 4,
          pointerEvents: 'none',
        }}
      >
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Icon source={CREDIT_ICON} size={26} color={rgba(color, 0.5)} />
          <Animated.Text style={{
            fontFamily: 'ShareTechMono_400Regular',
            fontSize: 64,
            color,
            lineHeight: 68,
            transform: [{ scale: scaleAnim }],
          }}>
            {displayValue}
          </Animated.Text>
        </View>
        {label && (
          <Text style={{ fontSize: 10, letterSpacing: 1.5, color: rgba(color, 0.5), fontFamily: 'Rajdhani_600SemiBold' }}>
            {label}
          </Text>
        )}
      </View>
      {/* Pending pill — top-right, only when pending !== 0 */}
      {pending !== 0 && (
        <View
          style={{
            position: 'absolute', top: 6, right: 8,
            backgroundColor: rgba(pillColor, 0.18),
            borderWidth: 1, borderColor: rgba(pillColor, 0.50),
            borderRadius: 10, paddingVertical: 2, paddingHorizontal: 7,
            pointerEvents: 'none',
          }}
        >
          <Text style={{
            fontFamily: 'ShareTechMono_400Regular',
            fontSize: 12, color: pillColor,
          }}>
            {pillLabel}
          </Text>
        </View>
      )}
      {/* Vertical divider between ± zones */}
      <View style={{
        position: 'absolute', top: '15%', bottom: '15%', left: '50%',
        width: 1, backgroundColor: rgba(color, 0.12),
      }} />
    </View>
  );
}
