import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { rgba } from '../theme';
import { digits } from './DigitText';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

interface Props {
  score: number;
  color: string;
  onChange: (delta: number) => void;
  // fillFromTop=true for Corp (score fills from top); false for Runner (fills from bottom)
  fillFromTop?: boolean;
  /** Agenda points needed to win = number of segments (default 7). */
  max?: number;
}

/** Column width of the agenda tug-of-war bar — shared so the win-target
    button in GameScreen aligns exactly under the bars. */
export const AGENDA_BAR_WIDTH = 28;

export function AgendaBar({ score, color, onChange, fillFromTop = true, max = 7 }: Props) {
  const MAX = max;
  const barWidth = AGENDA_BAR_WIDTH;
  // Batch rapid taps so a burst commits + logs once; the score updates live.
  const { pending, bump } = useBatchedDelta(onChange);
  const displayScore = score + pending;
  // Build segment array: index 0 is visually top, MAX-1 is visually bottom
  const segments = Array.from({ length: MAX }, (_, i) => {
    return fillFromTop ? i < displayScore : (MAX - 1 - i) < displayScore;
  });

  const scoreLabel = (
    <Text style={{
      fontFamily: 'ShareTechMono_400Regular',
      fontSize: 13, fontWeight: '700', color, lineHeight: 15,
    }}>
      {digits(displayScore)}
    </Text>
  );

  return (
    <View style={{ width: barWidth, alignItems: 'center', flexShrink: 0 }}>
      {fillFromTop && <View style={{ marginBottom: 3 }}>{scoreLabel}</View>}
      <Pressable
        onPress={() => bump(1)}
        onLongPress={() => bump(-1)}
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
      {!fillFromTop && <View style={{ marginTop: 3 }}>{scoreLabel}</View>}
    </View>
  );
}
