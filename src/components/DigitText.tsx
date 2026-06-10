import React from 'react';
import { Text } from 'react-native';

/**
 * Returns a number's characters as React children with every 6 and 9
 * underlined — the mono font draws a 9 as a rotated 6, which is unreadable at a
 * glance. Works for multi-digit values (16, 19, 29, 69 …); each 6/9 is
 * underlined individually, other digits stay plain.
 *
 * Use inside an existing <Text> so it keeps that text's styling:
 *   <Text style={numberStyle}>{digits(value)}</Text>
 */
export function digits(value: string | number): React.ReactNode {
  return String(value)
    .split('')
    .map((ch, i) =>
      ch === '6' || ch === '9' ? (
        <Text key={i} style={{ textDecorationLine: 'underline' }}>{ch}</Text>
      ) : (
        ch
      ),
    );
}
