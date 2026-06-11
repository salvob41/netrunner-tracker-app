import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { Faction, C, rgba } from '../theme';
import { FactionGlyph } from './FactionGlyph';
import { Icon } from './Icon';
import { digits } from './DigitText';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

const AGENDA_ICON = require('../assets/agenda.png');
const TAG_ICON = require('../assets/tag.png');
const BAD_PUB_ICON = require('../assets/bad_pub.png');

interface Props {
  /** Which side is the opponent (i.e. NOT the side the player is tracking). */
  oppSide: 'corp' | 'runner';
  oppFaction: Faction;
  /** Border / label tint — typically the opp side's faction color. */
  oppColor: string;
  oppAgenda: number;
  /** When opp is runner: their tag count. When opp is corp: their bad-pub count. */
  oppSecondary: number;
  /** Tap → +1, long-press → −1. Parent handles state update + log. */
  onSecondaryDelta: (delta: number) => void;
  /** Landscape header has less vertical room — use compact sizing. */
  compact?: boolean;
}

export function OppChip({
  oppSide, oppFaction, oppColor, oppAgenda,
  oppSecondary, onSecondaryDelta, compact = false,
}: Props) {
  const s = compact
    ? { gap: 5, padY: 3, padX: 7, radius: 6, sepH: 10, glyph: 14, icon: 10, font: 11, labelFs: 7, innerGap: 3 }
    : { gap: 6, padY: 5, padX: 9, radius: 8, sepH: 12, glyph: 16, icon: 12, font: 13, labelFs: 8, innerGap: 4 };

  const oppIsCorp = oppSide === 'corp';
  const secondaryIcon = oppIsCorp ? BAD_PUB_ICON : TAG_ICON;
  const secondaryColor = oppIsCorp ? C.badpub : C.gold;

  // Batch rapid taps so a burst commits + logs once (like the credit token),
  // while the displayed count updates optimistically per tap.
  const { pending, bump } = useBatchedDelta(onSecondaryDelta);
  const displaySecondary = Math.max(0, oppSecondary + pending);

  return (
    <View style={{
      flexDirection: 'row', alignItems: 'center', gap: s.gap,
      paddingVertical: s.padY, paddingHorizontal: s.padX, borderRadius: s.radius,
      backgroundColor: rgba(oppColor, 0.06),
      borderWidth: 1, borderStyle: 'dashed', borderColor: rgba(oppColor, 0.4),
    }}>
      <Text style={{ fontSize: s.labelFs, letterSpacing: 1.5, color: rgba(oppColor, 0.75), fontFamily: 'Rajdhani_700Bold' }}>OPP</Text>
      <View style={{ width: 1, height: s.sepH, backgroundColor: rgba(C.dim, 0.4) }} />
      <FactionGlyph faction={oppFaction} size={s.glyph} />
      <Icon source={AGENDA_ICON} size={s.icon} color={rgba(C.gold, 0.7)} />
      <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: s.font, fontWeight: '700', color: C.gold }}>{digits(oppAgenda)}</Text>
      <Pressable
        onPress={() => bump(1)}
        onLongPress={() => bump(-1)}
        delayLongPress={400}
        style={{ flexDirection: 'row', alignItems: 'center', gap: s.innerGap }}
      >
        <Icon source={secondaryIcon} size={s.icon} color={rgba(secondaryColor, 0.7)} />
        <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: s.font, fontWeight: '700', color: secondaryColor }}>{digits(displaySecondary)}</Text>
      </Pressable>
    </View>
  );
}
