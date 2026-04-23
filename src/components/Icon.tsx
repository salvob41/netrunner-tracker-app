import React from 'react';
import { Image } from 'react-native';

interface IconProps {
  source: ReturnType<typeof require>;
  size?: number;
  color?: string;
}

export function Icon({ source, size = 18, color = '#ffffff' }: IconProps) {
  return (
    <Image
      source={source}
      style={{ width: size, height: size, tintColor: color }}
      resizeMode="contain"
    />
  );
}
