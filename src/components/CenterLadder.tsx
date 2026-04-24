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
  onCorpScore: () => void;
  onCorpDec: () => void;
  onRunnerScore: () => void;
  onRunnerDec: () => void;
}

const MAX = 7;

export function CenterLadder({
  corpScore, runnerScore, corpColor, runnerColor,
  onCorpScore, onCorpDec, onRunnerScore, onRunnerDec,
}: Props) {
  // Corp segments: fill from top (index 0 = top)
  const corpSegments = Array.from({ length: MAX }, (_, i) => i < corpScore);
  // Runner segments: fill from bottom (index 0 = top, so fill from MAX-1)
  const runnerSegments = Array.from({ length: MAX }, (_, i) => (MAX - 1 - i) < runnerScore);

  const handleCorpTap = (i: number, filled: boolean) => {
    // Tap unfilled → score+1, tap the last filled → score-1
    if (!filled) {
      onCorpScore();
    } else if (i === corpScore - 1) {
      onCorpDec();
    }
  };

  const handleRunnerTap = (i: number, filled: boolean) => {
    if (!filled) {
      onRunnerScore();
    } else if (i === MAX - runnerScore) {
      // The topmost filled runner segment
      onRunnerDec();
    }
  };

  return (
    <View style={{ width: 74, alignItems: 'center', flexShrink: 0, paddingVertical: 2 }}>
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

      {/* Corp segments */}
      <View style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}>
        {corpSegments.map((filled, i) => (
          <Pressable
            key={`c${i}`}
            onPressIn={() => handleCorpTap(i, filled)}
            style={{
              height: 10, maxHeight: 14, borderRadius: 3, width: '100%',
              backgroundColor: filled ? rgba(corpColor, 0.6) : rgba(corpColor, 0.08),
              borderWidth: 1,
              borderColor: rgba(corpColor, filled ? 0.45 : 0.12),
            }}
          />
        ))}
      </View>

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

      {/* Runner segments */}
      <View style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}>
        {runnerSegments.map((filled, i) => (
          <Pressable
            key={`r${i}`}
            onPressIn={() => handleRunnerTap(i, filled)}
            style={{
              height: 10, maxHeight: 14, borderRadius: 3, width: '100%',
              backgroundColor: filled ? rgba(runnerColor, 0.6) : rgba(runnerColor, 0.08),
              borderWidth: 1,
              borderColor: rgba(runnerColor, filled ? 0.45 : 0.12),
            }}
          />
        ))}
      </View>

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
