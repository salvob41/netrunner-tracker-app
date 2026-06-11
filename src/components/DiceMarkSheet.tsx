import React, { useEffect, useRef, useState } from 'react';
import { View, Text, Pressable, Animated, StyleSheet } from 'react-native';
import { C, rgba } from '../theme';
import { Mark } from '../state';

interface Props {
  /** Roll an n-sided die. Hook handles logging + haptics. */
  onRollDie: (sides: number) => number;
  /** Roll a mark (HQ/R&D/Archives). Hook handles logging + sets persistent chip. */
  onRollMark: () => Mark;
  onClose: () => void;
}

type DieKind = 'd2' | 'd3' | 'd6' | 'd20' | 'MARK';

const DICE: { kind: DieKind; sides: number }[] = [
  { kind: 'd2',  sides: 2 },
  { kind: 'd3',  sides: 3 },
  { kind: 'd6',  sides: 6 },
  { kind: 'd20', sides: 20 },
];

export function DiceMarkSheet({ onRollDie, onRollMark, onClose }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.92)).current;
  const resultScale = useRef(new Animated.Value(1)).current;
  const resultOpacity = useRef(new Animated.Value(1)).current;

  const [result, setResult] = useState<{ label: string; value: string } | null>(null);
  const [faces, setFaces] = useState(5);

  const MIN_FACES = 2;
  const MAX_FACES = 100;
  const stepFaces = (d: number) =>
    setFaces(n => Math.max(MIN_FACES, Math.min(MAX_FACES, n + d)));

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 1, duration: 180, useNativeDriver: false }),
      Animated.spring(scale, { toValue: 1, friction: 7, tension: 110, useNativeDriver: false }),
    ]).start();
  }, []);

  const close = () => {
    Animated.parallel([
      Animated.timing(opacity, { toValue: 0, duration: 150, useNativeDriver: false }),
      Animated.timing(scale, { toValue: 0.92, duration: 150, useNativeDriver: false }),
    ]).start(onClose);
  };

  const animateResult = () => {
    resultScale.setValue(0.6);
    resultOpacity.setValue(0);
    Animated.parallel([
      Animated.spring(resultScale, { toValue: 1, friction: 5, tension: 120, useNativeDriver: false }),
      Animated.timing(resultOpacity, { toValue: 1, duration: 180, useNativeDriver: false }),
    ]).start();
  };

  const handleDie = (label: string, sides: number) => {
    const v = onRollDie(sides);
    setResult({ label, value: String(v) });
    animateResult();
  };

  const handleMark = () => {
    const m = onRollMark();
    setResult({ label: 'MARK', value: m });
    animateResult();
  };

  return (
    <Animated.View style={[StyleSheet.absoluteFillObject, {
      backgroundColor: 'rgba(7,9,13,0.85)',
      opacity,
      justifyContent: 'center',
      alignItems: 'center',
      padding: 20,
      zIndex: 60,
      elevation: 60,
    }]}>
      <Pressable style={StyleSheet.absoluteFillObject} onPress={close} />
      <Animated.View style={{
        width: '100%',
        maxWidth: 360,
        backgroundColor: '#0d1119',
        borderRadius: 16,
        borderWidth: 1, borderColor: '#1a2535',
        transform: [{ scale }],
        paddingBottom: 16,
        overflow: 'hidden',
      }}>
        {/* Header */}
        <View style={{
          flexDirection: 'row', alignItems: 'center',
          padding: 12, paddingHorizontal: 16,
          borderBottomWidth: 1, borderBottomColor: '#1a2535',
        }}>
          <Text style={{
            fontSize: 10, letterSpacing: 2, fontWeight: '700',
            color: C.dim, fontFamily: 'Rajdhani_700Bold', flex: 1,
          }}>
            DICE · MARK
          </Text>
          <Pressable onPress={close} style={{ padding: 4, paddingHorizontal: 8 }}>
            <Text style={{ fontSize: 14, color: C.dim }}>✕</Text>
          </Pressable>
        </View>

        {/* Result display */}
        <View style={{
          minHeight: 110,
          alignItems: 'center', justifyContent: 'center',
          paddingVertical: 18,
        }}>
          {result ? (
            <Animated.View style={{
              alignItems: 'center',
              transform: [{ scale: resultScale }],
              opacity: resultOpacity,
            }}>
              <Text style={{
                fontSize: 10, letterSpacing: 2.5,
                color: rgba(C.gold, 0.6), fontFamily: 'Rajdhani_700Bold',
                marginBottom: 4,
              }}>
                {result.label}
              </Text>
              {/* Numeric results get an underline (6/9 dice convention); MARK string results don't. */}
              {/^\d+$/.test(result.value) ? (
                <View style={{ alignItems: 'center' }}>
                  <Text style={{
                    fontSize: 56, color: C.gold,
                    fontFamily: 'ShareTechMono_400Regular',
                    letterSpacing: 2,
                    lineHeight: 60,
                  }}>
                    {result.value}
                  </Text>
                  <View style={{
                    height: 3, width: '70%',
                    backgroundColor: C.gold,
                    marginTop: 2,
                    borderRadius: 1,
                  }} />
                </View>
              ) : (
                <Text style={{
                  fontSize: 56, color: C.gold,
                  fontFamily: 'ShareTechMono_400Regular',
                  letterSpacing: 2,
                }}>
                  {result.value}
                </Text>
              )}
            </Animated.View>
          ) : (
            <Text style={{
              fontSize: 11, letterSpacing: 2,
              color: C.dim, fontFamily: 'Rajdhani_600SemiBold',
            }}>
              TAP TO ROLL
            </Text>
          )}
        </View>

        {/* Buttons */}
        <View style={{
          flexDirection: 'row', gap: 8,
          paddingHorizontal: 16, paddingTop: 4,
        }}>
          {DICE.map(({ kind, sides }) => (
            <RollBtn
              key={kind}
              label={kind}
              color={C.gold}
              onPress={() => handleDie(kind, sides)}
            />
          ))}
        </View>
        {/* Custom face count — pick any number of sides, then roll */}
        <View style={{
          flexDirection: 'row', alignItems: 'center', gap: 8,
          paddingHorizontal: 16, paddingTop: 12,
        }}>
          <Text style={{
            fontSize: 10, letterSpacing: 2, color: C.dim,
            fontFamily: 'Rajdhani_700Bold',
          }}>
            FACES
          </Text>
          <StepBtn label="−" color={C.gold} onPress={() => stepFaces(-1)} />
          <Text style={{
            minWidth: 40, textAlign: 'center',
            fontSize: 20, color: C.gold,
            fontFamily: 'ShareTechMono_400Regular',
          }}>
            {faces}
          </Text>
          <StepBtn label="+" color={C.gold} onPress={() => stepFaces(1)} />
          <View style={{ flex: 1 }}>
            <RollBtn label={`ROLL d${faces}`} color={C.gold} onPress={() => handleDie(`d${faces}`, faces)} />
          </View>
        </View>

        <View style={{ paddingHorizontal: 16, paddingTop: 10 }}>
          <RollBtn label="MARK" color="#2fb8ff" wide onPress={handleMark} />
        </View>
      </Animated.View>
    </Animated.View>
  );
}

function RollBtn({
  label, color, onPress, wide = false,
}: {
  label: string;
  color: string;
  onPress: () => void;
  wide?: boolean;
}) {
  return (
    <Pressable
      onPressIn={onPress}
      style={{
        flex: wide ? undefined : 1,
        paddingVertical: 14,
        borderRadius: 10,
        borderWidth: 1.5, borderColor: rgba(color, 0.35),
        backgroundColor: rgba(color, 0.10),
        alignItems: 'center', justifyContent: 'center',
      }}
    >
      <Text style={{
        fontSize: 14, letterSpacing: 2,
        color, fontFamily: 'Rajdhani_700Bold',
      }}>
        {label}
      </Text>
    </Pressable>
  );
}

function StepBtn({ label, color, onPress }: { label: string; color: string; onPress: () => void }) {
  return (
    <Pressable
      onPressIn={onPress}
      hitSlop={6}
      style={{
        width: 34, height: 34, borderRadius: 8,
        borderWidth: 1.5, borderColor: rgba(color, 0.35),
        backgroundColor: rgba(color, 0.10),
        alignItems: 'center', justifyContent: 'center',
      }}
    >
      <Text style={{ fontSize: 20, lineHeight: 22, color, fontFamily: 'Rajdhani_700Bold' }}>
        {label}
      </Text>
    </Pressable>
  );
}
