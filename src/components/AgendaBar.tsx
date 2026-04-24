import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { rgba } from '../theme';

interface Props {
  score: number;
  color: string;
  onTap: () => void;
  onDec: () => void;
  // fillFromTop=true for Corp (score fills from top); false for Runner (fills from bottom)
  fillFromTop?: boolean;
}

export function AgendaBar({ score, color, onTap, onDec, fillFromTop = true }: Props) {
  const MAX = 7;
  const barWidth = 28;
  // Build segment array: index 0 is visually top, MAX-1 is visually bottom
  const segments = Array.from({ length: MAX }, (_, i) => {
    return fillFromTop ? i < score : (MAX - 1 - i) < score;
  });

  return (
    <View style={{ width: barWidth, alignItems: 'center', flexShrink: 0 }}>
      {fillFromTop && (
        <Text style={{
          fontFamily: 'ShareTechMono_400Regular',
          fontSize: 13, fontWeight: '700', color, lineHeight: 15, marginBottom: 3,
        }}>
          {score}
        </Text>
      )}
      <Pressable
        onPressIn={onTap}
        style={{ gap: 3, flex: 1, width: '100%' }}
      >
        {segments.map((filled, i) => (
          <View key={i} style={{
            flex: 1, borderRadius: 4, width: '100%',
            backgroundColor: filled ? rgba(color, 0.65) : rgba(color, 0.08),
            borderWidth: 1,
            borderColor: rgba(color, filled ? 0.5 : 0.14),
          }} />
        ))}
      </Pressable>
      <Pressable onPressIn={onDec} style={{ paddingVertical: 3, paddingHorizontal: 6 }}>
        <Text style={{ fontSize: 13, color: rgba(color, 0.4), lineHeight: 16 }}>−</Text>
      </Pressable>
      {!fillFromTop && (
        <Text style={{
          fontFamily: 'ShareTechMono_400Regular',
          fontSize: 13, fontWeight: '700', color, lineHeight: 15, marginTop: 3,
        }}>
          {score}
        </Text>
      )}
    </View>
  );
}
