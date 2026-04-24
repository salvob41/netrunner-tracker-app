import React from 'react';
import { Image, View } from 'react-native';
import { Faction, rgba } from '../theme';

const ICONS: Record<string, ReturnType<typeof require>> = {
  hb:       require('../assets/faction_hb.png'),
  jinteki:  require('../assets/faction_jinteki.png'),
  nbn:      require('../assets/faction_nbn.png'),
  weyland:  require('../assets/faction_weyland.png'),
  anarch:   require('../assets/faction_anarch.png'),
  criminal: require('../assets/faction_criminal.png'),
  shaper:   require('../assets/faction_shaper.png'),
};

interface Props {
  faction: Faction | null;
  size?: number;
}

export function FactionGlyph({ faction, size = 28 }: Props) {
  if (!faction) return null;
  const src = ICONS[faction.id];
  if (!src) return null;

  const iconSize = Math.round(size * 0.9);
  return (
    <View style={{
      width: size, height: size, borderRadius: 4,
      backgroundColor: rgba(faction.color, 0.12),
      alignItems: 'center', justifyContent: 'center',
    }}>
      <Image source={src} style={{ width: iconSize, height: iconSize }} resizeMode="contain" />
    </View>
  );
}
