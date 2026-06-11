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

export function MiniLadder({
  corpScore, runnerScore, corpColor, runnerColor,
  onCorpChange, onRunnerChange, max = 7, onOpenTarget,
}: Props) {
  const MAX = max;
  // Batch rapid taps per side so a burst commits + logs once; scores update live.
  const corp = useBatchedDelta(onCorpChange);
  const runner = useBatchedDelta(onRunnerChange);
  const dispCorp = corpScore + corp.pending;
  const dispRunner = runnerScore + runner.pending;
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
          {digits(dispCorp)}
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
        onPress={() => corp.bump(1)}
        onLongPress={() => corp.bump(-1)}
        delayLongPress={400}
        style={{ flex: 1, flexDirection: 'row', gap: 3, alignItems: 'center' }}
      >
        {Array.from({ length: MAX }, (_, i) => {
          const filled = i < dispCorp;
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

      {/* Center agenda icon — tap to open the agenda-to-win picker.
          zIndex keeps it above the flanking bar Pressables so taps land here
          (on web the adjacent flex Pressables can otherwise swallow the tap). */}
      <Pressable
        onPress={() => onOpenTarget?.()}
        style={{
          alignItems: 'center', paddingHorizontal: 6, paddingVertical: 3,
          borderRadius: 7, borderWidth: 1, borderColor: rgba(C.gold, 0.35),
          backgroundColor: rgba(C.gold, 0.08),
          zIndex: 10, elevation: 10,
        }}
      >
        <Icon source={AGENDA_ICON} size={12} color={C.gold} />
        <Text style={{
          fontSize: 10, letterSpacing: 0.5, marginTop: 1,
          color: C.gold, fontFamily: 'Rajdhani_700Bold',
        }}>
          {MAX}
        </Text>
      </Pressable>

      {/* Runner bars — fill from right toward center; tap +1, long-press −1 */}
      <Pressable
        onPress={() => runner.bump(1)}
        onLongPress={() => runner.bump(-1)}
        delayLongPress={400}
        style={{ flex: 1, flexDirection: 'row', gap: 3, alignItems: 'center' }}
      >
        {Array.from({ length: MAX }, (_, i) => {
          const filled = (MAX - 1 - i) < dispRunner;
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
          {digits(dispRunner)}
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
