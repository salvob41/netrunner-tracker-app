import React, { useState } from 'react';
import { View, Text, Pressable, ScrollView } from 'react-native';
import { FactionGlyph } from '../components/FactionGlyph';
import { CORP_FACTIONS, RUNNER_FACTIONS, Faction, C, rgba } from '../theme';

interface Props {
  onStart: (corp: Faction, runner: Faction) => void;
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
  faction, selected, onSelect,
}: {
  faction: Faction;
  selected: boolean;
  onSelect: (f: Faction) => void;
}) {
  return (
    <Pressable
      onPressIn={() => onSelect(faction)}
      style={{
        padding: 14, paddingHorizontal: 10, borderRadius: 10,
        alignItems: 'center', gap: 8,
        backgroundColor: selected ? rgba(faction.color, 0.12) : 'rgba(255,255,255,0.03)',
        borderWidth: selected ? 2 : 1.5,
        borderColor: selected ? faction.color : 'rgba(255,255,255,0.07)',
      }}
    >
      <FactionGlyph faction={faction} size={36} />
      <Text style={{
        fontSize: 11, fontWeight: '700', letterSpacing: 1, textAlign: 'center',
        color: selected ? faction.color : C.dim,
        fontFamily: 'Rajdhani_700Bold', lineHeight: 14,
      }}>
        {faction.name}
      </Text>
    </Pressable>
  );
}

export function SetupScreen({ onStart, bg }: Props) {
  const [corpFaction, setCorpFaction] = useState<Faction | null>(null);
  const [runnerFaction, setRunnerFaction] = useState<Faction | null>(null);

  const ready = corpFaction !== null && runnerFaction !== null;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: bg }}
      contentContainerStyle={{ padding: 24, paddingBottom: 32 }}
    >
      {/* Title block */}
      <View style={{ alignItems: 'center', marginBottom: 32 }}>
        <Text style={{ fontSize: 9, letterSpacing: 4, color: C.dim, fontFamily: 'Rajdhani_600SemiBold', marginBottom: 6 }}>
          ANDROID
        </Text>
        <Text style={{ fontSize: 28, fontWeight: '700', letterSpacing: 3, color: C.text, fontFamily: 'Rajdhani_700Bold' }}>
          NETRUNNER
        </Text>
        <Text style={{ fontSize: 11, letterSpacing: 2, color: C.dim, fontFamily: 'Rajdhani_600SemiBold' }}>
          GAME TRACKER
        </Text>
      </View>

      {/* Corp faction picker — 2-column grid */}
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

      {/* Runner faction picker — 3 equal columns */}
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

      {/* Start button — only active when both factions selected */}
      <Pressable
        onPressIn={() => ready && onStart(corpFaction!, runnerFaction!)}
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
