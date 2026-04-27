import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Icon } from './Icon';
import { C, rgba } from '../theme';

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

export function CenterLadder({
  corpScore, runnerScore, corpColor, runnerColor,
  onCorpChange, onRunnerChange,
}: Props) {
  // Corp segments: fill from top (index 0 = top)
  const corpSegments = Array.from({ length: MAX }, (_, i) => i < corpScore);
  // Runner segments: fill from bottom (index 0 = top, so fill from MAX-1)
  const runnerSegments = Array.from({ length: MAX }, (_, i) => (MAX - 1 - i) < runnerScore);

  return (
    <View style={{ width: 48, alignItems: 'center', flexShrink: 0, paddingVertical: 2 }}>
      {/* Corp score label */}
      <Text style={{
        fontFamily: 'ShareTechMono_400Regular',
        fontSize: 16, fontWeight: '700', color: corpColor, lineHeight: 18,
      }}>
        {corpScore}
      </Text>
      <Text style={{
        fontFamily: 'Rajdhani_700Bold', fontSize: 8, letterSpacing: 2,
        color: rgba(corpColor, 0.5), marginBottom: 3,
      }}>
        CORP
      </Text>

      {/* Corp segments — tap +1, long press -1 */}
      <Pressable
        onPress={() => onCorpChange(1)}
        onLongPress={() => onCorpChange(-1)}
        delayLongPress={400}
        style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}
      >
        {corpSegments.map((filled, i) => (
          <View
            key={`c${i}`}
            style={{
              height: 10, maxHeight: 14, borderRadius: 3, width: '100%',
              backgroundColor: filled ? rgba(corpColor, 0.6) : rgba(corpColor, 0.08),
              borderWidth: 1,
              borderColor: rgba(corpColor, filled ? 0.45 : 0.12),
            }}
          />
        ))}
      </Pressable>

      {/* Center agenda icon */}
      <View style={{ paddingVertical: 5, alignItems: 'center' }}>
        <Icon source={AGENDA_ICON} size={20} color={C.gold} />
        <Text style={{
          fontSize: 6, letterSpacing: 0.5, marginTop: 1,
          color: rgba(C.gold, 0.5), fontFamily: 'Rajdhani_700Bold',
        }}>
          7 WIN
        </Text>
      </View>

      {/* Runner segments — tap +1, long press -1 */}
      <Pressable
        onPress={() => onRunnerChange(1)}
        onLongPress={() => onRunnerChange(-1)}
        delayLongPress={400}
        style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}
      >
        {runnerSegments.map((filled, i) => (
          <View
            key={`r${i}`}
            style={{
              height: 10, maxHeight: 14, borderRadius: 3, width: '100%',
              backgroundColor: filled ? rgba(runnerColor, 0.6) : rgba(runnerColor, 0.08),
              borderWidth: 1,
              borderColor: rgba(runnerColor, filled ? 0.45 : 0.12),
            }}
          />
        ))}
      </Pressable>

      {/* Runner score label */}
      <Text style={{
        fontFamily: 'Rajdhani_700Bold', fontSize: 8, letterSpacing: 2,
        color: rgba(runnerColor, 0.5), marginTop: 3,
      }}>
        RUNNER
      </Text>
      <Text style={{
        fontFamily: 'ShareTechMono_400Regular',
        fontSize: 16, fontWeight: '700', color: runnerColor, lineHeight: 18,
      }}>
        {runnerScore}
      </Text>
    </View>
  );
}
