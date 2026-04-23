import React from 'react';
import { View, Text } from 'react-native';
import { Faction, rgba } from '../theme';

interface Props {
  faction: Faction | null;
  size?: number;
}

export function FactionGlyph({ faction, size = 28 }: Props) {
  if (!faction) return null;
  return (
    <View style={{
      width: size, height: size, borderRadius: size / 2,
      backgroundColor: rgba(faction.color, 0.18),
      borderWidth: 1.5, borderColor: rgba(faction.color, 0.5),
      alignItems: 'center', justifyContent: 'center',
    }}>
      <Text style={{
        fontSize: Math.round(size * 0.44),
        fontWeight: '700',
        color: faction.color,
        fontFamily: 'Rajdhani_700Bold',
        // lineHeight must match fontSize on Android to avoid clipping
        lineHeight: Math.round(size * 0.5),
      }}>
        {faction.short[0]}
      </Text>
    </View>
  );
}
