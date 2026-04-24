import React, { useRef } from 'react';
import { Animated, Pressable } from 'react-native';
import { Icon } from './Icon';
import { rgba } from '../theme';

const CLICK_ICON = require('../assets/click.png');
const CLICK_SPENT_ICON = require('../assets/click_spent.png');

interface Props {
  filled: boolean;
  color: string;
  onTap?: () => void;
  size?: number;
  ghost?: boolean;
  radius?: number;
}

export function ClickToken({ filled, color, onTap, size = 48, ghost = false, radius = 8 }: Props) {
  const scale = useRef(new Animated.Value(1)).current;

  const handlePress = () => {
    if (!onTap) return;
    // Spring-bounce on tap for tactile feedback
    Animated.sequence([
      Animated.timing(scale, { toValue: 0.82, duration: 80, useNativeDriver: false }),
      Animated.timing(scale, { toValue: 1, duration: 120, useNativeDriver: false }),
    ]).start();
    onTap();
  };

  const bg = filled ? rgba(color, ghost ? 0.08 : 0.15) : 'transparent';
  const borderColor = filled ? rgba(color, ghost ? 0.5 : 0.7) : rgba(color, 0.22);
  const iconColor = rgba(color, filled ? 1 : 0.3);

  return (
    <Pressable onPressIn={handlePress}>
      <Animated.View style={{
        width: size, height: size, borderRadius: radius,
        backgroundColor: bg, borderWidth: 2, borderColor,
        alignItems: 'center', justifyContent: 'center',
        opacity: ghost ? 0.65 : 1,
        transform: [{ scale }],
      }}>
        <Icon
          source={filled ? CLICK_ICON : CLICK_SPENT_ICON}
          size={Math.round(size * 0.52)}
          color={iconColor}
        />
      </Animated.View>
    </Pressable>
  );
}
