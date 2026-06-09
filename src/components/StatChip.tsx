import React, { useEffect, useRef, useState } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { Icon } from './Icon';
import { C, rgba } from '../theme';
import { useBatchedDelta } from '../hooks/useBatchedDelta';

const PILL_GREEN = '#00f0a0';
const PILL_RED   = '#ff2040';

interface Props {
  iconSource: ReturnType<typeof require>;
  value: number;
  color: string;
  onChange: (delta: number) => void;
  chipHeight?: number;
  chipWidth?: number;
  /** When true, chip fills its parent flex container instead of using a fixed height. */
  flexHeight?: boolean;
  testID?: string;
}

const CHIP_WIDTH = 56;
const CHIP_HEIGHT = 40;

export function StatChip({ iconSource, value, color, onChange, chipHeight = CHIP_HEIGHT, chipWidth = CHIP_WIDTH, flexHeight = false, testID }: Props) {
  const popAnim = useRef(new Animated.Value(1)).current;
  const hintOpacity = useRef(new Animated.Value(0)).current;
  const { pending, bump } = useBatchedDelta(onChange);

  const displayValue = value + pending;
  const active = displayValue > 0;

  const pillColor = pending >= 0 ? PILL_GREEN : PILL_RED;
  const pillLabel = pending > 0 ? `+${pending}` : `−${Math.abs(pending)}`;

  // Show "Hold to remove" hint the first time this chip transitions from 0 to >0.
  const [showHint, setShowHint] = useState(false);
  const hintShownRef = useRef(false);
  const prevDisplayRef = useRef(displayValue);
  useEffect(() => {
    if (!hintShownRef.current && prevDisplayRef.current === 0 && displayValue > 0) {
      hintShownRef.current = true;
      setShowHint(true);
      Animated.sequence([
        Animated.timing(hintOpacity, { toValue: 1, duration: 200, useNativeDriver: false }),
        Animated.delay(2400),
        Animated.timing(hintOpacity, { toValue: 0, duration: 250, useNativeDriver: false }),
      ]).start(() => setShowHint(false));
    }
    prevDisplayRef.current = displayValue;
  }, [displayValue, hintOpacity]);

  const tap = (delta: number) => {
    bump(delta);
    Animated.sequence([
      Animated.timing(popAnim, { toValue: 1.3, duration: 70, useNativeDriver: false }),
      Animated.timing(popAnim, { toValue: 1, duration: 130, useNativeDriver: false }),
    ]).start();
  };

  // All chips are uniform 56×40 rectangles (wider than tall).
  // flexHeight lets the chip stretch vertically while keeping fixed width.
  const sizeStyle = flexHeight
    ? { flex: 1, width: chipWidth }
    : { height: chipHeight, width: chipWidth };

  return (
    <Pressable
      testID={testID}
      onPress={() => tap(+1)}
      onLongPress={() => tap(-1)}
      delayLongPress={400}
      style={[{
        borderRadius: 10,
        backgroundColor: rgba(color, active ? 0.14 : 0.06),
        borderWidth: 1, borderColor: rgba(color, active ? 0.50 : 0.22),
        alignItems: 'center', justifyContent: 'center',
      }, sizeStyle]}
    >
      <Icon source={iconSource} size={24} color={rgba(color, active ? 1 : 0.6)} />
      {active && (
        <Animated.View style={{
          position: 'absolute', top: -8, right: -8,
          minWidth: 24, height: 24, borderRadius: 12,
          paddingHorizontal: 6,
          backgroundColor: color,
          alignItems: 'center', justifyContent: 'center',
          transform: [{ scale: popAnim }],
        }}>
          <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: 14, fontWeight: '800', color: '#000', lineHeight: 16 }}>
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
      {showHint && (
        <Animated.View
          pointerEvents="none"
          style={{
            position: 'absolute', top: '100%', marginTop: 6,
            backgroundColor: '#0d1119',
            borderWidth: 1, borderColor: rgba(color, 0.5),
            borderRadius: 6, paddingVertical: 4, paddingHorizontal: 8,
            opacity: hintOpacity,
            zIndex: 100, elevation: 8,
            width: 160,
          }}
        >
          <Text
            numberOfLines={1}
            style={{
              fontSize: 10, color: C.text, fontFamily: 'Rajdhani_600SemiBold',
              letterSpacing: 0.5, textAlign: 'center',
            }}
          >
            Keep pressed to remove 1
          </Text>
        </Animated.View>
      )}
    </Pressable>
  );
}
