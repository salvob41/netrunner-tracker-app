import React, { useRef } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { Icon } from './Icon';
import { rgba } from '../theme';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

const PILL_GREEN = '#00f0a0';
const PILL_RED   = '#ff2040';

interface Props {
  iconSource: ReturnType<typeof require>;
  value: number;
  color: string;
  onChange: (delta: number) => void;
  chipHeight?: number;
  /** When true, chip fills its parent flex container instead of using a fixed height. */
  flexHeight?: boolean;
  testID?: string;
}

export function StatChip({ iconSource, value, color, onChange, chipHeight = 40, flexHeight = false, testID }: Props) {
  const popAnim = useRef(new Animated.Value(1)).current;
  const { pending, bump } = useBatchedDelta(onChange);

  const displayValue = value + pending;
  const active = displayValue > 0;

  const pillColor = pending >= 0 ? PILL_GREEN : PILL_RED;
  const pillLabel = pending > 0 ? `+${pending}` : `\u2212${Math.abs(pending)}`;

  const tap = (delta: number) => {
    bump(delta);
    Animated.sequence([
      Animated.timing(popAnim, { toValue: 1.3, duration: 70, useNativeDriver: false }),
      Animated.timing(popAnim, { toValue: 1, duration: 130, useNativeDriver: false }),
    ]).start();
  };

  const sizeStyle = flexHeight ? { flex: 1 } : { height: chipHeight };

  return (
    <Pressable
      testID={testID}
      onPress={() => tap(+1)}
      onLongPress={() => tap(-1)}
      delayLongPress={400}
      style={[{
        borderRadius: 9,
        backgroundColor: rgba(color, active ? 0.14 : 0.06),
        borderWidth: 1, borderColor: rgba(color, active ? 0.50 : 0.22),
        alignItems: 'center', justifyContent: 'center',
      }, sizeStyle]}
    >
      <Icon source={iconSource} size={22} color={rgba(color, active ? 1 : 0.6)} />
      {active && (
        <Animated.View style={{
          position: 'absolute', top: -7, right: -7,
          minWidth: 20, height: 20, borderRadius: 10,
          paddingHorizontal: 5,
          backgroundColor: color,
          alignItems: 'center', justifyContent: 'center',
          transform: [{ scale: popAnim }],
        }}>
          <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: 12, fontWeight: '800', color: '#000', lineHeight: 14 }}>
            {displayValue}
          </Text>
        </Animated.View>
      )}
      {pending !== 0 && (
        <View style={{
          position: 'absolute', bottom: 2, right: 2,
          backgroundColor: rgba(pillColor, 0.18),
          borderWidth: 1, borderColor: rgba(pillColor, 0.50),
          borderRadius: 8, paddingVertical: 1, paddingHorizontal: 5,
        }}>
          <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: 9, color: pillColor }}>
            {pillLabel}
          </Text>
        </View>
      )}
    </Pressable>
  );
}
