import React from 'react';
import { View } from 'react-native';

interface Props {
  size?: number;
  color: string;
}

/** Stylized rounded-square die face with 5 pips. Used as the dice-tools entry button. */
export function DieIcon({ size = 22, color }: Props) {
  const s = size;
  const pip = s * 0.10;
  const inset = s * 0.26;
  const positions: [number, number][] = [
    [inset, inset],
    [s - inset, inset],
    [s / 2, s / 2],
    [inset, s - inset],
    [s - inset, s - inset],
  ];
  const stroke = Math.max(1, s * 0.07);
  return (
    <View
      style={{
        width: s,
        height: s,
        borderWidth: stroke,
        borderColor: color,
        borderRadius: s * 0.18,
      }}
    >
      {positions.map(([x, y], i) => (
        <View
          key={i}
          style={{
            position: 'absolute',
            // offset by stroke so pip centers align with the inner (border-box) coords
            left: x - pip - stroke,
            top: y - pip - stroke,
            width: pip * 2,
            height: pip * 2,
            borderRadius: pip,
            backgroundColor: color,
          }}
        />
      ))}
    </View>
  );
}
