import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { rgba } from '../theme';

interface Props {
  score: number;
  color: string;
  onChange: (delta: number) => void;
  // fillFromTop=true for Corp (score fills from top); false for Runner (fills from bottom)
  fillFromTop?: boolean;
}

export function AgendaBar({ score, color, onChange, fillFromTop = true }: Props) {
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
        onPress={() => onChange(1)}
        onLongPress={() => onChange(-1)}
        delayLongPress={400}
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
