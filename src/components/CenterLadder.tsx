import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Icon } from './Icon';
import { C, rgba } from '../theme';
import { digits } from './DigitText';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

const AGENDA_ICON = require('../assets/agenda.png');

interface Props {
  corpScore: number;
  runnerScore: number;
  corpColor: string;
  runnerColor: string;
  onCorpChange: (delta: number) => void;
  onRunnerChange: (delta: number) => void;
  /** Agenda points needed to win = number of ladder segments. */
  max?: number;
  /** Tap the center agenda symbol to open the win-target picker. */
  onOpenTarget?: () => void;
}

export function CenterLadder({
  corpScore, runnerScore, corpColor, runnerColor,
  onCorpChange, onRunnerChange, max = 7, onOpenTarget,
}: Props) {
  const MAX = max;
  // Batch rapid taps per side so a burst commits + logs once; scores update live.
  const corp = useBatchedDelta(onCorpChange);
  const runner = useBatchedDelta(onRunnerChange);
  const dispCorp = corpScore + corp.pending;
  const dispRunner = runnerScore + runner.pending;
  // Corp segments: fill from top (index 0 = top)
  const corpSegments = Array.from({ length: MAX }, (_, i) => i < dispCorp);
  // Runner segments: fill from bottom (index 0 = top, so fill from MAX-1)
  const runnerSegments = Array.from({ length: MAX }, (_, i) => (MAX - 1 - i) < dispRunner);

  return (
    <View style={{ width: 56, alignItems: 'center', flexShrink: 0, paddingVertical: 2 }}>
      {/* Corp score label */}
      <Text style={{
        fontFamily: 'ShareTechMono_400Regular',
        fontSize: 16, fontWeight: '700', color: corpColor, lineHeight: 18,
      }}>
        {digits(dispCorp)}
      </Text>
      <Text style={{
        fontFamily: 'Rajdhani_700Bold', fontSize: 8, letterSpacing: 2,
        color: rgba(corpColor, 0.5), marginBottom: 3,
      }}>
        CORP
      </Text>

      {/* Corp segments — tap +1, long press -1 */}
      <Pressable
        onPress={() => corp.bump(1)}
        onLongPress={() => corp.bump(-1)}
        delayLongPress={400}
        style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}
      >
        {corpSegments.map((filled, i) => (
          <View
            key={`c${i}`}
            style={{
              flex: 1, minHeight: 12, maxHeight: 20, borderRadius: 4, width: '100%',
              backgroundColor: filled ? rgba(corpColor, 0.6) : rgba(corpColor, 0.08),
              borderWidth: 1,
              borderColor: rgba(corpColor, filled ? 0.45 : 0.12),
            }}
          />
        ))}
      </Pressable>

      {/* Center agenda icon — tap to open the agenda-to-win picker.
          zIndex keeps it above the flanking segment Pressables so taps land here
          (on web the adjacent flex Pressables can otherwise swallow the tap). */}
      <Pressable
        onPress={() => onOpenTarget?.()}
        style={{
          // Full width so the button matches the ladder segments' column width.
          width: '100%', paddingVertical: 5, marginVertical: 2, alignItems: 'center',
          borderRadius: 8, borderWidth: 1, borderColor: rgba(C.gold, 0.35),
          backgroundColor: rgba(C.gold, 0.08),
          zIndex: 10, elevation: 10,
        }}
      >
        <Icon source={AGENDA_ICON} size={18} color={C.gold} />
        <Text style={{
          fontSize: 11, letterSpacing: 0.5, marginTop: 1,
          color: C.gold, fontFamily: 'Rajdhani_700Bold',
        }}>
          {MAX}
        </Text>
        <Text style={{
          fontSize: 6, letterSpacing: 0.5,
          color: rgba(C.gold, 0.55), fontFamily: 'Rajdhani_700Bold',
        }}>
          TO WIN
        </Text>
      </Pressable>

      {/* Runner segments — tap +1, long press -1 */}
      <Pressable
        onPress={() => runner.bump(1)}
        onLongPress={() => runner.bump(-1)}
        delayLongPress={400}
        style={{ gap: 3, width: '100%', flex: 1, justifyContent: 'center' }}
      >
        {runnerSegments.map((filled, i) => (
          <View
            key={`r${i}`}
            style={{
              flex: 1, minHeight: 12, maxHeight: 20, borderRadius: 4, width: '100%',
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
        {digits(dispRunner)}
      </Text>
    </View>
  );
}
