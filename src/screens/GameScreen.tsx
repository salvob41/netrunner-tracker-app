import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, Pressable, useWindowDimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ClickToken } from '../components/ClickToken';
import { CreditCounter } from '../components/CreditCounter';
import { StatChip } from '../components/StatChip';
import { AgendaBar } from '../components/AgendaBar';
import { LogSheet } from '../components/LogSheet';
import { WinOverlay } from '../components/WinOverlay';
import { FactionGlyph } from '../components/FactionGlyph';
import { Icon } from '../components/Icon';
import { Faction, C, rgba, Atmosphere } from '../theme';
import { makeInitialState, clamp, GameState } from '../state';

const CLICK_ICON = require('../assets/click.png');
const HAND_ICON = require('../assets/hand.png');
const CREDIT_ICON = require('../assets/credit.png');
const TAG_ICON = require('../assets/tag.png');
const BRAIN_ICON = require('../assets/core_damage.png');
const BAD_PUB_ICON = require('../assets/bad_pub.png');
const MU_ICON = require('../assets/mu.png');
const LINK_ICON = require('../assets/link.png');
const AGENDA_ICON = require('../assets/agenda.png');

interface Props {
  corpFaction: Faction;
  runnerFaction: Faction;
  onReset: () => void;
  theme: Atmosphere & { tokenRadius: number; inactiveOpacity: number };
}

/** Small icon+label button for one-click actions (draw, take credit). */
function ActionBtn({
  label, iconSource, color, onPress,
}: {
  label: string;
  iconSource: ReturnType<typeof require>;
  color: string;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPressIn={onPress}
      style={{
        flexDirection: 'column', alignItems: 'center', gap: 2,
        backgroundColor: rgba(color, 0.10),
        borderWidth: 1, borderColor: rgba(color, 0.35),
        borderRadius: 7, padding: 5, paddingHorizontal: 8, minWidth: 42,
      }}
    >
      <Icon source={iconSource} size={14} color={color} />
      <Text style={{
        fontSize: 9, fontWeight: '700', color,
        letterSpacing: 0.5, fontFamily: 'Rajdhani_700Bold',
      }}>
        {label}
      </Text>
    </Pressable>
  );
}

/** Cycles extra-click count (0→1→2→3→0). Shows badge when nonzero. */
function ExtraClickBtn({
  color, onPress, extra,
}: {
  color: string;
  onPress: () => void;
  extra: number;
}) {
  return (
    <Pressable
      onPressIn={onPress}
      style={{
        flexDirection: 'row', alignItems: 'center', gap: 3,
        backgroundColor: rgba(color, 0.08),
        borderWidth: 1, borderColor: rgba(color, 0.28),
        borderRadius: 7, padding: 5, paddingHorizontal: 7,
      }}
    >
      <Text style={{ fontSize: 9, fontWeight: '700', color, fontFamily: 'Rajdhani_700Bold' }}>+</Text>
      <Icon source={CLICK_ICON} size={11} color={color} />
      {extra > 0 && (
        <Text style={{ fontSize: 9, color, fontFamily: 'ShareTechMono_400Regular' }}>{extra}</Text>
      )}
    </Pressable>
  );
}

export function GameScreen({ corpFaction, runnerFaction, onReset, theme }: Props) {
  const [gs, setGs] = useState<GameState>(makeInitialState);
  const [showLog, setShowLog] = useState(false);
  const [corpFlipped, setCorpFlipped] = useState(false);
  const [runnerFlipped, setRunnerFlipped] = useState(false);
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;

  // Flush refs for credit counters — called before any turn transition.
  const corpCreditFlush = React.useRef<() => void>(() => {});
  const runnerCreditFlush = React.useRef<() => void>(() => {});

  const update = (fn: (s: GameState) => GameState) => setGs(prev => fn(prev));

  // Stable log appender — avoids re-creating closures in child handlers
  const addLog = useCallback((player: 'corp' | 'runner' | 'game', message: string) => {
    setGs(prev => ({
      ...prev,
      log: [...prev.log, { round: prev.round, player, message }],
    }));
  }, []);

  // Check win condition after each agenda change
  useEffect(() => {
    if (gs.corp.agenda >= 7 && !gs.winner) {
      update(s => ({ ...s, winner: 'corp' }));
    } else if (gs.runner.agenda >= 7 && !gs.winner) {
      update(s => ({ ...s, winner: 'runner' }));
    }
  }, [gs.corp.agenda, gs.runner.agenda, gs.winner]);

  const handleEndTurn = () => {
    corpCreditFlush.current();
    runnerCreditFlush.current();
    update(s => {
      if (s.active === 'corp') {
        return {
          ...s,
          active: 'runner',
          corp: { ...s.corp, extra: 0 },
          runner: { ...s.runner, clicks: 4 + s.runner.extra },
          log: [...s.log, { round: s.round, player: 'game', message: 'Corp turn ended · Runner begins' }],
        };
      } else {
        const nextRound = s.round + 1;
        return {
          ...s,
          round: nextRound,
          active: 'corp',
          runner: { ...s.runner, extra: 0 },
          corp: { ...s.corp, clicks: 3 + s.corp.extra },
          log: [...s.log, {
            round: s.round, player: 'game',
            message: `Round ${s.round} complete · Round ${nextRound} begins`,
          }],
        };
      }
    });
  };

  const corpColor = corpFaction?.color || theme.corp;
  const runnerColor = runnerFaction?.color || theme.runner;
  const activeColor = gs.active === 'corp' ? corpColor : runnerColor;
  // Hand size = base 5, reduced by brain damage, increased by bonus cards
  const handSize = Math.max(0, 5 - gs.runner.brain + gs.runner.handBonus);

  const handleCorpTokenTap = (i: number, filled: boolean) => {
    if (gs.active !== 'corp') return;
    if (filled) {
      update(s => ({ ...s, corp: { ...s.corp, clicks: Math.max(0, s.corp.clicks - 1) } }));
      addLog('corp', 'Click spent');
    } else {
      update(s => ({
        ...s,
        corp: { ...s.corp, clicks: Math.min(3 + s.corp.extra, s.corp.clicks + 1) },
      }));
    }
  };

  const handleRunnerTokenTap = (i: number, filled: boolean) => {
    if (gs.active !== 'runner') return;
    if (filled) {
      update(s => ({ ...s, runner: { ...s.runner, clicks: Math.max(0, s.runner.clicks - 1) } }));
      addLog('runner', 'Click spent');
    } else {
      update(s => ({
        ...s,
        runner: { ...s.runner, clicks: Math.min(4 + s.runner.extra, s.runner.clicks + 1) },
      }));
    }
  };

  const handleNewGame = () => {
    setGs(makeInitialState());
    onReset();
  };

  return (
    <View style={{
      flex: 1, backgroundColor: theme.bg,
      paddingTop: insets.top + 8,
      paddingBottom: insets.bottom + 8,
      paddingHorizontal: 12,
      gap: 5,
    }}>

      {/* Turn banner */}
      <View style={{
        borderRadius: 10, paddingVertical: 8, paddingHorizontal: 14, flexShrink: 0,
        backgroundColor: rgba(activeColor, 0.08),
        borderWidth: 1, borderColor: rgba(activeColor, 0.3),
        flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <View>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
            <Icon source={CLICK_ICON} size={16} color={activeColor} />
            <Text style={{
              fontFamily: 'Rajdhani_700Bold', fontSize: 14,
              letterSpacing: 2.5, color: activeColor,
            }}>
              {gs.active === 'corp' ? 'CORP TURN' : 'RUNNER TURN'}
            </Text>
          </View>
          <Text style={{
            fontFamily: 'Rajdhani_600SemiBold', fontSize: 10,
            letterSpacing: 1.5, color: C.dim,
          }}>
            ROUND {gs.round}
          </Text>
        </View>
        <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center' }}>
          <Pressable
            onPressIn={onReset}
            style={{
              padding: 6, paddingHorizontal: 10, borderRadius: 6,
              borderWidth: 1, borderColor: rgba(C.red, 0.2),
            }}
          >
            <Text style={{
              fontSize: 10, letterSpacing: 1,
              color: rgba(C.red, 0.55), fontFamily: 'Rajdhani_700Bold',
            }}>
              ⟳ RESET
            </Text>
          </Pressable>
        </View>
      </View>

      {/* Corp panel + agenda sidebar */}
      <View style={{ flexDirection: 'row', gap: 7, flex: 5, minHeight: 0 }}>
        <View style={{
          flex: 1, borderRadius: 12, padding: 10,
          backgroundColor: gs.active === 'corp' ? rgba(corpColor, 0.06) : theme.panel,
          borderWidth: gs.active === 'corp' ? 2 : 1,
          borderColor: rgba(corpColor, gs.active === 'corp' ? 0.6 : 0.2),
          opacity: gs.active === 'runner' ? theme.inactiveOpacity : 1,
          transform: corpFlipped ? [{ rotate: '180deg' }] : [],
        }}>
          {/* Panel header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <View style={{ width: 3, height: 16, borderRadius: 2, backgroundColor: corpColor }} />
            <FactionGlyph faction={corpFaction} size={22} />
            <Text style={{
              fontFamily: 'Rajdhani_700Bold', fontSize: 13, letterSpacing: 2, color: corpColor,
            }}>
              {corpFaction?.name || 'CORP'}
            </Text>
            <View style={{ flex: 1 }} />
            <Pressable
              onPressIn={() => setCorpFlipped(v => !v)}
              style={{
                padding: 4, paddingHorizontal: 7, borderRadius: 6,
                borderWidth: 1,
                borderColor: rgba(corpColor, corpFlipped ? 0.5 : 0.2),
                backgroundColor: corpFlipped ? rgba(corpColor, 0.12) : 'transparent',
              }}
            >
              <Text style={{ fontSize: 11, color: rgba(corpColor, corpFlipped ? 0.9 : 0.4) }}>⇅</Text>
            </Pressable>
            {gs.active === 'corp' && (
              <View style={{ flexDirection: 'row', gap: 6 }}>
                <ActionBtn
                  label="Draw" iconSource={HAND_ICON} color={corpColor}
                  onPress={() => {
                    if (gs.corp.clicks > 0) {
                      update(s => ({ ...s, corp: { ...s.corp, clicks: s.corp.clicks - 1 } }));
                      addLog('corp', 'Drew a card');
                    }
                  }}
                />
                <ActionBtn
                  label="+¢" iconSource={CREDIT_ICON} color={corpColor}
                  onPress={() => {
                    if (gs.corp.clicks > 0) {
                      update(s => ({
                        ...s,
                        corp: { ...s.corp, clicks: s.corp.clicks - 1, credits: s.corp.credits + 1 },
                      }));
                      addLog('corp', 'Took 1¢');
                    }
                  }}
                />
              </View>
            )}
          </View>

          {/* Click tokens */}
          <View style={{ flexDirection: 'row', gap: 6, marginBottom: 8, flexWrap: 'wrap' }}>
            {Array.from({ length: 3 + gs.corp.extra }, (_, i) => (
              <ClickToken
                key={i}
                filled={i < gs.corp.clicks}
                color={corpColor}
                onTap={gs.active === 'corp'
                  ? () => handleCorpTokenTap(i, i < gs.corp.clicks)
                  : undefined}
                ghost={i >= 3}
                size={i >= 3 ? 38 : 46}
                radius={theme.tokenRadius}
              />
            ))}
          </View>

          {/* Credits + Bad Pub — flex: 1 fills remaining panel height */}
          <View style={{ flex: 1, flexDirection: 'row', gap: 8 }}>
            <CreditCounter
              value={gs.corp.credits}
              color={corpColor}
              flushRef={corpCreditFlush}
              onChange={d => {
                update(s => {
                  const next = clamp(s.corp.credits + d, 0, 99);
                  const sign = d > 0 ? '+' : '';
                  return {
                    ...s,
                    corp: { ...s.corp, credits: next },
                    log: [...s.log, { round: s.round, player: 'corp', message: `Credits ${sign}${d} → ${next}¢` }],
                  };
                });
              }}
            />
            <View style={{ justifyContent: 'center', width: isLandscape ? 80 : 65 }}>
              <StatChip
                iconSource={BAD_PUB_ICON}
                value={gs.corp.badPub}
                color={C.badpub}
                onChange={d => {
                  update(s => ({ ...s, corp: { ...s.corp, badPub: clamp(s.corp.badPub + d, 0, 99) } }));
                  addLog('corp', d > 0 ? 'Bad pub +1' : 'Bad pub −1');
                }}
                label="BAD PUB"
              />
            </View>
          </View>

          {/* Extra click cycle button */}
          <View style={{ alignItems: 'flex-end', marginTop: 6 }}>
            <ExtraClickBtn
              color={corpColor}
              extra={gs.corp.extra}
              onPress={() => update(s => {
                const prev = s.corp.extra;
                const next = (prev + 1) % 4;
                const dc = next > prev ? 1 : -prev;
                return { ...s, corp: { ...s.corp, extra: next, clicks: Math.max(0, s.corp.clicks + dc) } };
              })}
            />
          </View>
        </View>

        <AgendaBar
          score={gs.corp.agenda}
          color={corpColor}
          fillFromTop={true}
          onTap={() => {
            update(s => ({
              ...s,
              corp: { ...s.corp, agenda: clamp(s.corp.agenda + 1, 0, 99) },
            }));
            addLog('corp', 'Scored agenda +1');
          }}
          onDec={() => {
            update(s => ({ ...s, corp: { ...s.corp, agenda: clamp(s.corp.agenda - 1, 0, 99) } }));
            addLog('corp', 'Agenda −1');
          }}
        />
      </View>

      {/* End Turn button row */}
      <View style={{ flexDirection: 'row', gap: 7, flexShrink: 0 }}>
        <Pressable
          onPressIn={handleEndTurn}
          style={{
            flex: 1, borderRadius: 10, padding: 12,
            alignItems: 'center', justifyContent: 'center',
            flexDirection: 'row', gap: 8,
            backgroundColor: rgba(theme.green, 0.10),
            borderWidth: 1, borderColor: rgba(theme.green, 0.45),
          }}
        >
          <Icon source={CLICK_ICON} size={14} color={theme.green} />
          <Text style={{
            fontSize: 12, fontWeight: '700', letterSpacing: 2.5,
            color: theme.green, fontFamily: 'Rajdhani_700Bold',
          }}>
            END {gs.active === 'corp' ? 'CORP' : 'RUNNER'} TURN
          </Text>
        </Pressable>
        {/* Win condition reminder — width matches agenda bar (28px) */}
        <View style={{ width: 28, alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <Icon source={AGENDA_ICON} size={16} color={C.gold} />
          <Text style={{
            fontSize: 6, letterSpacing: 0.5,
            color: rgba(C.gold, 0.55), fontFamily: 'Rajdhani_700Bold',
          }}>
            7WIN
          </Text>
        </View>
      </View>

      {/* Runner panel + agenda sidebar */}
      <View style={{ flexDirection: 'row', gap: 7, flex: 6, minHeight: 0 }}>
        <View style={{
          flex: 1, borderRadius: 12, padding: 10,
          backgroundColor: gs.active === 'runner' ? rgba(runnerColor, 0.06) : theme.panel,
          borderWidth: gs.active === 'runner' ? 2 : 1,
          borderColor: rgba(runnerColor, gs.active === 'runner' ? 0.6 : 0.2),
          opacity: gs.active === 'corp' ? theme.inactiveOpacity : 1,
          transform: runnerFlipped ? [{ rotate: '180deg' }] : [],
        }}>
          {/* Panel header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <View style={{ width: 3, height: 16, borderRadius: 2, backgroundColor: runnerColor }} />
            <FactionGlyph faction={runnerFaction} size={22} />
            <Text style={{
              fontFamily: 'Rajdhani_700Bold', fontSize: 13, letterSpacing: 2, color: runnerColor,
            }}>
              {runnerFaction?.name || 'RUNNER'}
            </Text>
            <View style={{ flex: 1 }} />
            <Pressable
              onPressIn={() => setRunnerFlipped(v => !v)}
              style={{
                padding: 4, paddingHorizontal: 7, borderRadius: 6,
                borderWidth: 1,
                borderColor: rgba(runnerColor, runnerFlipped ? 0.5 : 0.2),
                backgroundColor: runnerFlipped ? rgba(runnerColor, 0.12) : 'transparent',
              }}
            >
              <Text style={{ fontSize: 11, color: rgba(runnerColor, runnerFlipped ? 0.9 : 0.4) }}>⇅</Text>
            </Pressable>
            {gs.active === 'runner' && (
              <View style={{ flexDirection: 'row', gap: 6 }}>
                <ActionBtn
                  label="Draw" iconSource={HAND_ICON} color={runnerColor}
                  onPress={() => {
                    if (gs.runner.clicks > 0) {
                      update(s => ({ ...s, runner: { ...s.runner, clicks: s.runner.clicks - 1 } }));
                      addLog('runner', 'Drew a card');
                    }
                  }}
                />
                <ActionBtn
                  label="+¢" iconSource={CREDIT_ICON} color={runnerColor}
                  onPress={() => {
                    if (gs.runner.clicks > 0) {
                      update(s => ({
                        ...s,
                        runner: { ...s.runner, clicks: s.runner.clicks - 1, credits: s.runner.credits + 1 },
                      }));
                      addLog('runner', 'Took 1¢');
                    }
                  }}
                />
              </View>
            )}
          </View>

          {/* Click tokens */}
          <View style={{ flexDirection: 'row', gap: 5, marginBottom: 8, flexWrap: 'wrap' }}>
            {Array.from({ length: 4 + gs.runner.extra }, (_, i) => (
              <ClickToken
                key={i}
                filled={i < gs.runner.clicks}
                color={runnerColor}
                onTap={gs.active === 'runner'
                  ? () => handleRunnerTokenTap(i, i < gs.runner.clicks)
                  : undefined}
                ghost={i >= 4}
                size={i >= 4 ? 35 : 42}
                radius={theme.tokenRadius}
              />
            ))}
          </View>

          {/* Credits + 2-col stat grid — flex: 1 fills remaining panel height */}
          <View style={{ flex: 1, flexDirection: 'row', gap: 8 }}>
            <CreditCounter
              value={gs.runner.credits}
              color={runnerColor}
              flushRef={runnerCreditFlush}
              onChange={d => {
                update(s => {
                  const next = clamp(s.runner.credits + d, 0, 99);
                  const sign = d > 0 ? '+' : '';
                  return {
                    ...s,
                    runner: { ...s.runner, credits: next },
                    log: [...s.log, { round: s.round, player: 'runner', message: `Credits ${sign}${d} → ${next}¢` }],
                  };
                });
              }}
            />
            {/* Single-column stat chips — same compact style as corp BadPub */}
            <View style={{ gap: 4, width: isLandscape ? 160 : 125 }}>
              <View style={{ flex: 1 }}>
                <StatChip
                  iconSource={TAG_ICON} value={gs.runner.tags} color={C.gold} flexHeight
                  onChange={d => {
                    update(s => ({ ...s, runner: { ...s.runner, tags: clamp(s.runner.tags + d, 0, 99) } }));
                    addLog('runner', d > 0 ? 'Tag +1' : 'Tag −1');
                  }}
                />
              </View>
              <View style={{ flex: 1 }}>
                <StatChip
                  iconSource={BRAIN_ICON} value={gs.runner.brain} color={C.purple} flexHeight
                  onChange={d => {
                    update(s => ({ ...s, runner: { ...s.runner, brain: clamp(s.runner.brain + d, 0, 99) } }));
                    addLog('runner', d > 0 ? 'Core damage +1' : 'Core damage −1');
                  }}
                />
              </View>
              <View style={{ flex: 1 }}>
                <StatChip
                  iconSource={HAND_ICON} value={handSize} color={runnerColor} flexHeight
                  onChange={d => {
                    update(s => ({ ...s, runner: { ...s.runner, handBonus: clamp(s.runner.handBonus + d, -5, 10) } }));
                    addLog('runner', d > 0 ? 'Hand size +1' : 'Hand size −1');
                  }}
                />
              </View>
              <View style={{ flex: 1 }}>
                <StatChip
                  iconSource={MU_ICON} value={gs.runner.mu} color={C.mu} flexHeight
                  onChange={d => {
                    update(s => ({ ...s, runner: { ...s.runner, mu: clamp(s.runner.mu + d, 0, 12) } }));
                    addLog('runner', d > 0 ? 'MU +1' : 'MU −1');
                  }}
                />
              </View>
              <View style={{ flex: 1 }}>
                <StatChip
                  iconSource={LINK_ICON} value={gs.runner.link} color={C.link} flexHeight
                  onChange={d => {
                    update(s => ({ ...s, runner: { ...s.runner, link: clamp(s.runner.link + d, 0, 99) } }));
                    addLog('runner', d > 0 ? 'Link +1' : 'Link −1');
                  }}
                />
              </View>
            </View>
          </View>

          {/* Extra click button — same layout as corp */}
          <View style={{ alignItems: 'flex-end', marginTop: 6 }}>
            <ExtraClickBtn
              color={runnerColor}
              extra={gs.runner.extra}
              onPress={() => update(s => {
                const prev = s.runner.extra;
                const next = (prev + 1) % 5;
                const dc = next > prev ? 1 : -prev;
                return { ...s, runner: { ...s.runner, extra: next, clicks: Math.max(0, s.runner.clicks + dc) } };
              })}
            />
          </View>
        </View>

        <AgendaBar
          score={gs.runner.agenda}
          color={runnerColor}
          fillFromTop={false}
          onTap={() => {
            update(s => ({
              ...s,
              runner: { ...s.runner, agenda: clamp(s.runner.agenda + 1, 0, 99) },
            }));
            addLog('runner', 'Stole agenda +1');
          }}
          onDec={() => {
            update(s => ({ ...s, runner: { ...s.runner, agenda: clamp(s.runner.agenda - 1, 0, 99) } }));
            addLog('runner', 'Agenda −1');
          }}
        />
      </View>

      {/* Game log bar — tap to open slide-up sheet */}
      <View style={{ flexShrink: 0 }}>
        <Pressable
          onPressIn={() => setShowLog(true)}
          style={{
            borderRadius: 10, padding: 11, paddingHorizontal: 16,
            backgroundColor: theme.panel,
            borderWidth: 1, borderColor: rgba(C.gold, 0.25),
            flexDirection: 'row', alignItems: 'center', gap: 10,
          }}
        >
          <Icon source={AGENDA_ICON} size={16} color={rgba(C.gold, 0.7)} />
          <Text style={{
            fontSize: 11, color: C.text, fontFamily: 'Rajdhani_700Bold',
            letterSpacing: 2, flex: 1,
          }}>
            GAME LOG
          </Text>
          <Text style={{
            fontSize: 10, color: C.gold,
            fontFamily: 'ShareTechMono_400Regular', fontWeight: '600',
          }}>
            {gs.log.length}
          </Text>
          <Text style={{ fontSize: 12, color: C.dim }}>▲</Text>
        </Pressable>
      </View>

      {/* Overlays */}
      {showLog && <LogSheet log={gs.log} onClose={() => setShowLog(false)} />}
      {gs.winner && (
        <WinOverlay
          winner={gs.winner}
          corpFaction={corpFaction}
          runnerFaction={runnerFaction}
          onReset={handleNewGame}
        />
      )}
    </View>
  );
}
