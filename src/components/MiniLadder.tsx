import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Icon } from './Icon';
import { C, rgba } from '../theme';
import { digits } from './DigitText';

const AGENDA_ICON = require('../assets/agenda.png');

interface Props {
  corpScore: number;
  runnerScore: number;
  corpColor: string;
  runnerColor: string;
  onCorpChange: (delta: number) => void;
  onRunnerChange: (delta: number) => void;
}

const MAX = 7;

export function MiniLadder({
  corpScore, runnerScore, corpColor, runnerColor,
  onCorpChange, onRunnerChange,
}: Props) {
  return (
    <View style={{
      flexShrink: 0, paddingVertical: 8, paddingHorizontal: 12,
      borderRadius: 10, backgroundColor: '#0d1119',
      borderWidth: 1, borderColor: rgba(C.gold, 0.2),
      flexDirection: 'row', alignItems: 'center', gap: 10,
    }}>
      <View style={{ alignItems: 'center' }}>
        <Text style={{
          fontFamily: 'ShareTechMono_400Regular', fontSize: 14,
          fontWeight: '700', color: corpColor,
        }}>
          {digits(corpScore)}
        </Text>
        <Text style={{
          fontSize: 7, letterSpacing: 1, color: rgba(corpColor, 0.5),
          fontFamily: 'Rajdhani_700Bold',
        }}>
          CORP
        </Text>
      </View>

      {/* Corp bars — tap +1, long-press −1 */}
      <Pressable
        onPress={() => onCorpChange(1)}
        onLongPress={() => onCorpChange(-1)}
        delayLongPress={400}
        style={{ flex: 1, flexDirection: 'row', gap: 3, alignItems: 'center' }}
      >
        {Array.from({ length: MAX }, (_, i) => {
          const filled = i < corpScore;
          return (
            <View
              key={`c${i}`}
              style={{
                flex: 1, height: 8, borderRadius: 2,
                backgroundColor: filled ? rgba(corpColor, 0.7) : rgba(corpColor, 0.1),
                borderWidth: 1,
                borderColor: rgba(corpColor, filled ? 0.6 : 0.18),
              }}
            />
          );
        })}
      </Pressable>

      <Icon source={AGENDA_ICON} size={11} color={rgba(C.gold, 0.6)} />

      {/* Runner bars — fill from right toward center; tap +1, long-press −1 */}
      <Pressable
        onPress={() => onRunnerChange(1)}
        onLongPress={() => onRunnerChange(-1)}
        delayLongPress={400}
        style={{ flex: 1, flexDirection: 'row', gap: 3, alignItems: 'center' }}
      >
        {Array.from({ length: MAX }, (_, i) => {
          const filled = (MAX - 1 - i) < runnerScore;
          return (
            <View
              key={`r${i}`}
              style={{
                flex: 1, height: 8, borderRadius: 2,
                backgroundColor: filled ? rgba(runnerColor, 0.7) : rgba(runnerColor, 0.1),
                borderWidth: 1,
                borderColor: rgba(runnerColor, filled ? 0.6 : 0.18),
              }}
            />
          );
        })}
      </Pressable>

      <View style={{ alignItems: 'center' }}>
        <Text style={{
          fontFamily: 'ShareTechMono_400Regular', fontSize: 14,
          fontWeight: '700', color: runnerColor,
        }}>
          {digits(runnerScore)}
        </Text>
        <Text style={{
          fontSize: 7, letterSpacing: 1, color: rgba(runnerColor, 0.5),
          fontFamily: 'Rajdhani_700Bold',
        }}>
          RUN
        </Text>
      </View>
    </View>
  );
}
