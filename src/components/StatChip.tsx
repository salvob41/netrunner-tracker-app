import React, { useState, useRef } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { Icon } from './Icon';
import { rgba } from '../theme';

interface Props {
  iconSource: ReturnType<typeof require>;
  value: number;
  color: string;
  onChange: (delta: number) => void;
  label?: string;
}

export function StatChip({ iconSource, value, color, onChange, label }: Props) {
  const [expanded, setExpanded] = useState(false);
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const tap = (delta: number) => {
    onChange(delta);
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 1.2, duration: 70, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 130, useNativeDriver: true }),
    ]).start();
  };

  // Collapsed: shows only icon; tap to expand into ±/value controls
  if (!expanded) {
    return (
      <Pressable
        onPressIn={() => setExpanded(true)}
        style={{
          flex: 1, height: 56, borderRadius: 8,
          alignItems: 'center', justifyContent: 'center',
          backgroundColor: rgba(color, 0.08),
          borderWidth: 1, borderColor: rgba(color, 0.22),
        }}
      >
        <Icon source={iconSource} size={22} color={rgba(color, 0.75)} />
      </Pressable>
    );
  }

  return (
    <View style={{
      flex: 1, height: 56, borderRadius: 8, flexDirection: 'row',
      alignItems: 'center', overflow: 'hidden',
      backgroundColor: rgba(color, 0.10),
      borderWidth: 1.5, borderColor: rgba(color, 0.45),
    }}>
      <Pressable
        onPressIn={() => tap(-1)}
        style={{ width: 32, height: '100%', alignItems: 'center', justifyContent: 'center' }}
      >
        <Text style={{ color: rgba(color, 0.6), fontSize: 18 }}>−</Text>
      </Pressable>
      {/* Tap center to collapse back to icon view */}
      <Pressable
        onPressIn={() => setExpanded(false)}
        style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2 }}
      >
        <Icon source={iconSource} size={16} color={rgba(color, 0.7)} />
        <Animated.Text style={{
          fontFamily: 'ShareTechMono_400Regular',
          fontSize: 20,
          color,
          lineHeight: 24,
          transform: [{ scale: scaleAnim }],
        }}>
          {value}
        </Animated.Text>
      </Pressable>
      <Pressable
        onPressIn={() => tap(+1)}
        style={{ width: 32, height: '100%', alignItems: 'center', justifyContent: 'center' }}
      >
        <Text style={{ color: rgba(color, 0.6), fontSize: 18 }}>+</Text>
      </Pressable>
    </View>
  );
}
