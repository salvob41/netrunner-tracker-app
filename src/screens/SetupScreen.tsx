import React, { useState } from 'react';
import { View, Text, Pressable, ScrollView, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { FactionGlyph } from '../components/FactionGlyph';
import { CORP_FACTIONS, RUNNER_FACTIONS, Faction, PlayMode, C, rgba } from '../theme';

interface Props {
  onStart: (corp: Faction, runner: Faction, mode: PlayMode) => void;
  bg: string;
}

function SectionLabel({ label, color, done }: { label: string; color: string; done: boolean }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <View style={{ width: 3, height: 12, borderRadius: 2, backgroundColor: color }} />
      <Text style={{ fontSize: 10, letterSpacing: 2.5, fontWeight: '700', color, fontFamily: 'Rajdhani_700Bold' }}>
        {label}
      </Text>
      {done && (
        <Text style={{ fontSize: 10, color: rgba(color, 0.6), fontFamily: 'Rajdhani_500Medium' }}>✓</Text>
      )}
    </View>
  );
}

function FactionCard({
  faction, selected, onSelect, compact,
}: {
  faction: Faction;
  selected: boolean;
  onSelect: (f: Faction) => void;
  compact?: boolean;
}) {
  return (
    <Pressable
      onPressIn={() => onSelect(faction)}
      style={{
        padding: compact ? 8 : 14, paddingHorizontal: compact ? 6 : 10, borderRadius: compact ? 8 : 10,
        alignItems: 'center', gap: compact ? 4 : 8,
        backgroundColor: selected ? rgba(faction.color, 0.12) : 'rgba(255,255,255,0.03)',
        borderWidth: selected ? 2 : 1.5,
        borderColor: selected ? faction.color : 'rgba(255,255,255,0.07)',
      }}
    >
      <FactionGlyph faction={faction} size={compact ? 24 : 36} />
      <Text style={{
        fontSize: compact ? 9 : 11, fontWeight: '700', letterSpacing: 1, textAlign: 'center',
        color: selected ? faction.color : C.dim,
        fontFamily: 'Rajdhani_700Bold', lineHeight: compact ? 11 : 14,
      }}>
        {faction.name}
      </Text>
    </Pressable>
  );
}

function ModePill({ label, active, color, onPress }: { label: string; active: boolean; color: string; onPress: () => void }) {
  return (
    <Pressable
      onPressIn={onPress}
      style={{
        flex: 1, paddingVertical: 7, borderRadius: 6, alignItems: 'center',
        backgroundColor: active ? rgba(color, 0.15) : 'transparent',
        borderWidth: 1,
        borderColor: active ? rgba(color, 0.5) : 'rgba(255,255,255,0.06)',
      }}
    >
      <Text style={{
        fontSize: 10, fontWeight: '700', letterSpacing: 2,
        color: active ? color : C.dim, fontFamily: 'Rajdhani_700Bold',
      }}>
        {label}
      </Text>
    </Pressable>
  );
}

export function SetupScreen({ onStart, bg }: Props) {
  const [corpFaction, setCorpFaction] = useState<Faction | null>(null);
  const [runnerFaction, setRunnerFaction] = useState<Faction | null>(null);
  const [mode, setMode] = useState<PlayMode>('both');
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;
  const insets = useSafeAreaInsets();

  const showCorp = mode !== 'runner';
  const showRunner = mode !== 'corp';
  const ready =
    (showCorp ? corpFaction !== null : true) &&
    (showRunner ? runnerFaction !== null : true);

  const handleModeChange = (m: PlayMode) => {
    setMode(m);
    if (m === 'runner') setCorpFaction(null);
    if (m === 'corp') setRunnerFaction(null);
  };

  const handleStartPress = () => {
    if (!ready) return;
    const corp = corpFaction ?? { id: '', name: 'CORP', short: 'C', color: '#2fb8ff' };
    const runner = runnerFaction ?? { id: '', name: 'RUNNER', short: 'R', color: '#ff5020' };
    onStart(corp, runner, mode);
  };

  if (isLandscape) {
    return (
      <View style={{
        flex: 1, backgroundColor: bg,
        paddingTop: insets.top + 6,
        paddingBottom: insets.bottom + 6,
        paddingLeft: insets.left + 12,
        paddingRight: insets.right + 12,
        gap: 8,
      }}>
        {/* Compact title */}
        <View style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 16, fontWeight: '700', letterSpacing: 3, color: C.text, fontFamily: 'Rajdhani_700Bold' }}>
            TRACKSTER TAKA
          </Text>
        </View>

        {/* Mode toggle */}
        <View style={{ flexDirection: 'row', gap: 6 }}>
          <ModePill label="BOTH" active={mode === 'both'} color="#00f0a0" onPress={() => handleModeChange('both')} />
          <ModePill label="CORP" active={mode === 'corp'} color="#2fb8ff" onPress={() => handleModeChange('corp')} />
          <ModePill label="RUNNER" active={mode === 'runner'} color="#ff5020" onPress={() => handleModeChange('runner')} />
        </View>

        {/* Side-by-side: Corp | Runner */}
        <View style={{ flex: 1, flexDirection: 'row', gap: 20, minHeight: 0, alignItems: 'center' }}>
          {showCorp && (
            <View style={{ flex: 4 }}>
              <SectionLabel label="CORPORATION" color="#2fb8ff" done={corpFaction !== null} />
              <View style={{ flexDirection: 'row', gap: 6 }}>
                {CORP_FACTIONS.map(f => (
                  <View key={f.id} style={{ flex: 1 }}>
                    <FactionCard
                      faction={f}
                      selected={corpFaction?.id === f.id}
                      onSelect={setCorpFaction}
                      compact
                    />
                  </View>
                ))}
              </View>
            </View>
          )}

          {showCorp && showRunner && (
            <View style={{ width: 1, height: '60%', backgroundColor: rgba('#ffffff', 0.06) }} />
          )}

          {showRunner && (
            <View style={{ flex: 3 }}>
              <SectionLabel label="RUNNER" color="#ff5020" done={runnerFaction !== null} />
              <View style={{ flexDirection: 'row', gap: 6 }}>
                {RUNNER_FACTIONS.map(f => (
                  <View key={f.id} style={{ flex: 1 }}>
                    <FactionCard
                      faction={f}
                      selected={runnerFaction?.id === f.id}
                      onSelect={setRunnerFaction}
                      compact
                    />
                  </View>
                ))}
              </View>
            </View>
          )}
        </View>

        {/* Start button */}
        <Pressable
          onPressIn={handleStartPress}
          style={{
            width: '100%', padding: 10, borderRadius: 8, alignItems: 'center', flexShrink: 0,
            backgroundColor: ready ? rgba('#00f0a0', 0.15) : 'rgba(255,255,255,0.04)',
            borderWidth: 1,
            borderColor: ready ? rgba('#00f0a0', 0.5) : 'rgba(255,255,255,0.08)',
          }}
        >
          <Text style={{
            color: ready ? '#00f0a0' : C.dim,
            fontFamily: 'Rajdhani_700Bold', fontSize: 13, letterSpacing: 3,
          }}>
            ▶ START GAME
          </Text>
        </Pressable>
      </View>
    );
  }

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: bg }}
      contentContainerStyle={{ padding: 24, paddingBottom: 32 }}
    >
      {/* Title block */}
      <View style={{ alignItems: 'center', marginBottom: 24 }}>
        <Text style={{ fontSize: 9, letterSpacing: 4, color: C.dim, fontFamily: 'Rajdhani_600SemiBold', marginBottom: 6 }}>
          UNOFFICIAL
        </Text>
        <Text style={{ fontSize: 28, fontWeight: '700', letterSpacing: 3, color: C.text, fontFamily: 'Rajdhani_700Bold' }}>
          TRACKSTER TAKA
        </Text>
        <Text style={{ fontSize: 11, letterSpacing: 2, color: C.dim, fontFamily: 'Rajdhani_600SemiBold' }}>
          NETRUNNER COMPANION
        </Text>
      </View>

      {/* Mode toggle */}
      <View style={{ flexDirection: 'row', gap: 8, marginBottom: 24 }}>
        <ModePill label="BOTH" active={mode === 'both'} color="#00f0a0" onPress={() => handleModeChange('both')} />
        <ModePill label="CORP" active={mode === 'corp'} color="#2fb8ff" onPress={() => handleModeChange('corp')} />
        <ModePill label="RUNNER" active={mode === 'runner'} color="#ff5020" onPress={() => handleModeChange('runner')} />
      </View>

      {/* Corp faction picker — 2-column grid */}
      {showCorp && (
        <>
          <SectionLabel label="CORPORATION" color="#2fb8ff" done={corpFaction !== null} />
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 24 }}>
            {CORP_FACTIONS.map(f => (
              <View key={f.id} style={{ width: '47%' }}>
                <FactionCard
                  faction={f}
                  selected={corpFaction?.id === f.id}
                  onSelect={setCorpFaction}
                />
              </View>
            ))}
          </View>
        </>
      )}

      {/* Runner faction picker — 3 equal columns */}
      {showRunner && (
        <>
          <SectionLabel label="RUNNER" color="#ff5020" done={runnerFaction !== null} />
          <View style={{ flexDirection: 'row', gap: 10, marginBottom: 32 }}>
            {RUNNER_FACTIONS.map(f => (
              <View key={f.id} style={{ flex: 1 }}>
                <FactionCard
                  faction={f}
                  selected={runnerFaction?.id === f.id}
                  onSelect={setRunnerFaction}
                />
              </View>
            ))}
          </View>
        </>
      )}

      {/* Start button */}
      <Pressable
        onPressIn={handleStartPress}
        style={{
          width: '100%', padding: 16, borderRadius: 10, alignItems: 'center',
          backgroundColor: ready ? rgba('#00f0a0', 0.15) : 'rgba(255,255,255,0.04)',
          borderWidth: 1,
          borderColor: ready ? rgba('#00f0a0', 0.5) : 'rgba(255,255,255,0.08)',
        }}
      >
        <Text style={{
          color: ready ? '#00f0a0' : C.dim,
          fontFamily: 'Rajdhani_700Bold', fontSize: 15, letterSpacing: 3,
        }}>
          ▶ START GAME
        </Text>
      </Pressable>
    </ScrollView>
  );
}
