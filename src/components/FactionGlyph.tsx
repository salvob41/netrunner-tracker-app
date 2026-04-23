import React from 'react';
import { View } from 'react-native';
import { SvgProps } from 'react-native-svg';
import { Faction, rgba } from '../theme';

// Static imports — metro can't resolve dynamic require paths for SVG assets
import HBIcon       from '../assets/faction_hb.svg';
import JintekiIcon  from '../assets/faction_jinteki.svg';
import NBNIcon      from '../assets/faction_nbn.svg';
import WeylandIcon  from '../assets/faction_weyland.svg';
import AnarchIcon   from '../assets/faction_anarch.svg';
import CriminalIcon from '../assets/faction_criminal.svg';
import ShaperIcon   from '../assets/faction_shaper.svg';

const ICONS: Record<string, React.FC<SvgProps>> = {
  hb:       HBIcon,
  jinteki:  JintekiIcon,
  nbn:      NBNIcon,
  weyland:  WeylandIcon,
  anarch:   AnarchIcon,
  criminal: CriminalIcon,
  shaper:   ShaperIcon,
};

interface Props {
  faction: Faction | null;
  size?: number;
}

export function FactionGlyph({ faction, size = 28 }: Props) {
  if (!faction) return null;
  const Icon = ICONS[faction.id];
  if (!Icon) return null;

  // Render icon slightly inset so edge-hugging paths aren't clipped
  const iconSize = Math.round(size * 0.88);
  return (
    <View style={{
      width: size, height: size, borderRadius: 4,
      backgroundColor: rgba(faction.color, 0.12),
      alignItems: 'center', justifyContent: 'center',
    }}>
      <Icon width={iconSize} height={iconSize} />
    </View>
  );
}
