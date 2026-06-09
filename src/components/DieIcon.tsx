import React from 'react';
import Svg, { Rect, Circle } from 'react-native-svg';

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
    <Svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>
      <Rect
        x={stroke / 2}
        y={stroke / 2}
        width={s - stroke}
        height={s - stroke}
        rx={s * 0.18}
        ry={s * 0.18}
        fill="transparent"
        stroke={color}
        strokeWidth={stroke}
      />
      {positions.map(([x, y], i) => (
        <Circle key={i} cx={x} cy={y} r={pip} fill={color} />
      ))}
    </Svg>
  );
}
