import React, { useState, useRef } from 'react';
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
  label?: string;
  chipHeight?: number;
  /** When true, chip fills its parent flex container instead of using a fixed height. */
  flexHeight?: boolean;
}

export function StatChip({ iconSource, value, color, onChange, label, chipHeight = 40, flexHeight = false }: Props) {
  const [expanded, setExpanded] = useState(false);
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const { pending, bump } = useBatchedDelta(onChange);

  const displayValue = value + pending;
  const pillColor = pending >= 0 ? PILL_GREEN : PILL_RED;
  const pillLabel = pending > 0 ? `+${pending}` : `\u2212${Math.abs(pending)}`;

  const tap = (delta: number) => {
    bump(delta);
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 1.2, duration: 70, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 130, useNativeDriver: true }),
    ]).start();
  };

  const sizeStyle = flexHeight ? {} : { height: chipHeight };

  // Collapsed: shows only icon (+ pending pill if mid-burst); tap to expand into ±/value controls
  if (!expanded) {
    return (
      <Pressable
        onPressIn={() => setExpanded(true)}
        style={[{
          flex: 1, borderRadius: 8,
          alignItems: 'center', justifyContent: 'center',
          backgroundColor: rgba(color, 0.08),
          borderWidth: 1, borderColor: rgba(color, 0.22),
        }, sizeStyle]}
      >
        <Icon source={iconSource} size={18} color={rgba(color, 0.75)} />
        {pending !== 0 && (
          <View
            pointerEvents="none"
            style={{
              position: 'absolute', top: 2, right: 2,
              backgroundColor: rgba(pillColor, 0.18),
              borderWidth: 1, borderColor: rgba(pillColor, 0.50),
              borderRadius: 8, paddingVertical: 1, paddingHorizontal: 5,
            }}
          >
            <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: 9, color: pillColor }}>
              {pillLabel}
            </Text>
          </View>
        )}
      </Pressable>
    );
  }

  return (
    <View style={[{
      flex: 1, borderRadius: 8, flexDirection: 'row',
      alignItems: 'center', overflow: 'hidden',
      backgroundColor: rgba(color, 0.10),
      borderWidth: 1.5, borderColor: rgba(color, 0.45),
    }, sizeStyle]}>
      <Pressable
        onPressIn={() => tap(-1)}
        style={{ width: 28, height: '100%', alignItems: 'center', justifyContent: 'center' }}
      >
        <Text style={{ color: rgba(color, 0.6), fontSize: 16 }}>−</Text>
      </Pressable>
      {/* Tap center to collapse back to icon view — icon + number shown inline */}
      <Pressable
        onLongPress={() => setExpanded(false)}
        style={{ flex: 1, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 4 }}
      >
        <Icon source={iconSource} size={14} color={rgba(color, 0.7)} />
        <Animated.Text style={{
          fontFamily: 'ShareTechMono_400Regular',
          fontSize: 20,
          color,
          lineHeight: 24,
          transform: [{ scale: scaleAnim }],
        }}>
          {displayValue}
        </Animated.Text>
        {pending !== 0 && (
          <Text style={{ fontFamily: 'ShareTechMono_400Regular', fontSize: 9, color: pillColor, marginLeft: 2 }}>
            {pillLabel}
          </Text>
        )}
      </Pressable>
      <Pressable
        onPressIn={() => tap(+1)}
        style={{ width: 28, height: '100%', alignItems: 'center', justifyContent: 'center' }}
      >
        <Text style={{ color: rgba(color, 0.6), fontSize: 16 }}>+</Text>
      </Pressable>
    </View>
  );
}
