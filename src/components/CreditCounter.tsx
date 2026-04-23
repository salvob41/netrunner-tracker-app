import React, { useRef } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { Icon } from './Icon';
import { rgba } from '../theme';

const CREDIT_ICON = require('../assets/credit.png');

interface Props {
  value: number;
  color: string;
  onChange: (delta: number) => void;
  label?: string;
}

export function CreditCounter({ value, color, onChange, label }: Props) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const tap = (delta: number) => {
    onChange(delta);
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 1.22, duration: 80, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 140, useNativeDriver: true }),
    ]).start();
  };

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
        }}
        pointerEvents="none"
      >
        <Icon source={CREDIT_ICON} size={22} color={rgba(color, 0.6)} />
        <Animated.Text style={{
          fontFamily: 'ShareTechMono_400Regular',
          fontSize: 64,
          color,
          lineHeight: 68,
          transform: [{ scale: scaleAnim }],
        }}>
          {value}
        </Animated.Text>
        {label && (
          <Text style={{ fontSize: 10, letterSpacing: 1.5, color: rgba(color, 0.5), fontFamily: 'Rajdhani_600SemiBold' }}>
            {label}
          </Text>
        )}
      </View>
      {/* Vertical divider between ± zones */}
      <View style={{
        position: 'absolute', top: '15%', bottom: '15%', left: '50%',
        width: 1, backgroundColor: rgba(color, 0.12),
      }} />
    </View>
  );
}
