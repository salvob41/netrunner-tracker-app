import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ClickToken } from '../components/ClickToken';
import { CreditCounter } from '../components/CreditCounter';
import { StatChip } from '../components/StatChip';
import { CenterLadder } from '../components/CenterLadder';
import { LogSheet } from '../components/LogSheet';
import { WinOverlay } from '../components/WinOverlay';
import { FactionGlyph } from '../components/FactionGlyph';
import { Icon } from '../components/Icon';
import { C, rgba } from '../theme';
import { clamp } from '../state';
import { GameHook } from '../hooks/useGameState';

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
  game: GameHook;
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
        flexDirection: 'column', alignItems: 'center', gap: 1,
        backgroundColor: rgba(color, 0.10),
        borderWidth: 1, borderColor: rgba(color, 0.35),
        borderRadius: 6, padding: 4, paddingHorizontal: 6, minWidth: 36,
      }}
    >
      <Icon source={iconSource} size={12} color={color} />
      <Text style={{
        fontSize: 8, fontWeight: '700', color,
        letterSpacing: 0.5, fontFamily: 'Rajdhani_700Bold',
      }}>
        {label}
      </Text>
    </Pressable>
  );
}

/** Cycles extra-click count. Shows badge when nonzero. */
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
        borderRadius: 6, padding: 4, paddingHorizontal: 6,
      }}
    >
      <Text style={{ fontSize: 8, fontWeight: '700', color, fontFamily: 'Rajdhani_700Bold' }}>+</Text>
      <Icon source={CLICK_ICON} size={10} color={color} />
      {extra > 0 && (
        <Text style={{ fontSize: 8, color, fontFamily: 'ShareTechMono_400Regular' }}>{extra}</Text>
      )}
    </Pressable>
  );
}

export function GameScreenLandscape({ game }: Props) {
  const {
    gs, update, addLog,
    showLog, setShowLog,
    corpFlipped, setCorpFlipped,
    runnerFlipped, setRunnerFlipped,
    corpCreditFlush, runnerCreditFlush,
    handleEndTurn, handleCorpTokenTap, handleRunnerTokenTap, handleNewGame,
    corpColor, runnerColor, activeColor, handSize,
    corpFaction, runnerFaction, onReset, theme,
  } = game;

  const insets = useSafeAreaInsets();

  return (
    <View style={{
      flex: 1, backgroundColor: theme.bg,
      paddingTop: insets.top + 4,
      paddingBottom: insets.bottom + 4,
      paddingLeft: insets.left + 8,
      paddingRight: insets.right + 8,
      gap: 4,
    }}>

      {/* Top bar */}
      <View style={{
        borderRadius: 8, paddingVertical: 5, paddingHorizontal: 10, flexShrink: 0,
        backgroundColor: rgba(activeColor, 0.08),
        borderWidth: 1, borderColor: rgba(activeColor, 0.3),
        flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Icon source={CLICK_ICON} size={14} color={activeColor} />
          <Text style={{
            fontFamily: 'Rajdhani_700Bold', fontSize: 12,
            letterSpacing: 2.5, color: activeColor,
          }}>
            {gs.active === 'corp' ? 'CORP TURN' : 'RUNNER TURN'}
          </Text>
          <Text style={{
            fontFamily: 'Rajdhani_600SemiBold', fontSize: 10,
            letterSpacing: 1.5, color: C.dim,
          }}>
            ROUND {gs.round}
          </Text>
        </View>
        <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center' }}>
          <Pressable
            onPress={() => setShowLog(true)}
            style={{
              padding: 4, paddingHorizontal: 8, borderRadius: 6,
              borderWidth: 1, borderColor: rgba(C.gold, 0.25),
              backgroundColor: rgba(C.gold, 0.06),
              flexDirection: 'row', alignItems: 'center', gap: 5,
            }}
          >
            <Icon source={AGENDA_ICON} size={12} color={rgba(C.gold, 0.7)} />
            <Text style={{
              fontSize: 9, color: C.text, fontFamily: 'Rajdhani_700Bold', letterSpacing: 1,
            }}>LOG</Text>
            <Text style={{
              fontSize: 9, color: C.gold, fontFamily: 'ShareTechMono_400Regular',
            }}>{gs.log.length}</Text>
          </Pressable>
          <Pressable
            onPressIn={onReset}
            style={{
              padding: 4, paddingHorizontal: 8, borderRadius: 6,
              borderWidth: 1, borderColor: rgba(C.red, 0.2),
            }}
          >
            <Text style={{
              fontSize: 9, letterSpacing: 1,
              color: rgba(C.red, 0.55), fontFamily: 'Rajdhani_700Bold',
            }}>
              RESET
            </Text>
          </Pressable>
        </View>
      </View>

      {/* Main row: Corp | Ladder | Runner */}
      <View style={{ flex: 1, flexDirection: 'row', gap: 6, minHeight: 0 }}>

        {/* Corp panel */}
        <View style={{
          flex: 1, borderRadius: 10, padding: 8,
          backgroundColor: gs.active === 'corp' ? rgba(corpColor, 0.06) : theme.panel,
          borderWidth: gs.active === 'corp' ? 2 : 1,
          borderColor: rgba(corpColor, gs.active === 'corp' ? 0.6 : 0.2),
          opacity: gs.active === 'runner' ? theme.inactiveOpacity : 1,
        }}>
          {/* Header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <View style={{ width: 3, height: 14, borderRadius: 2, backgroundColor: corpColor, transform: corpFlipped ? [{ rotate: '180deg' }] : [] }} />
            <View style={{ transform: corpFlipped ? [{ rotate: '180deg' }] : [] }}>
              <FactionGlyph faction={corpFaction} size={18} />
            </View>
            <Text style={{
              fontFamily: 'Rajdhani_700Bold', fontSize: 11, letterSpacing: 2, color: corpColor, flex: 1,
              transform: corpFlipped ? [{ rotate: '180deg' }] : [],
            }}>
              {corpFaction?.name || 'CORP'}
            </Text>
            <Pressable
              onPressIn={() => setCorpFlipped(v => !v)}
              style={{
                padding: 3, paddingHorizontal: 6, borderRadius: 5,
                borderWidth: 1,
                borderColor: rgba(corpColor, corpFlipped ? 0.5 : 0.2),
                backgroundColor: corpFlipped ? rgba(corpColor, 0.12) : 'transparent',
                transform: corpFlipped ? [{ rotate: '180deg' }] : [],
              }}
            >
              <Text style={{ fontSize: 10, color: rgba(corpColor, corpFlipped ? 0.9 : 0.4) }}>⇅</Text>
            </Pressable>
            {gs.active === 'corp' && (
              <View style={{ flexDirection: 'row', gap: 4, transform: corpFlipped ? [{ rotate: '180deg' }] : [] }}>
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
          <View style={{ flexDirection: 'row', gap: 4, marginBottom: 6, flexWrap: 'wrap' }}>
            {Array.from({ length: 3 + gs.corp.extra }, (_, i) => (
              <View key={i} style={{ transform: corpFlipped ? [{ rotate: '180deg' }] : [] }}>
                <ClickToken
                  filled={i < gs.corp.clicks}
                  color={corpColor}
                  onTap={gs.active === 'corp'
                    ? () => handleCorpTokenTap(i, i < gs.corp.clicks)
                    : undefined}
                  ghost={i >= 3}
                  size={i >= 3 ? 34 : 40}
                  radius={theme.tokenRadius}
                />
              </View>
            ))}
          </View>

          {/* Credits */}
          <View style={{ flex: 1, minHeight: 0, transform: corpFlipped ? [{ rotate: '180deg' }] : [] }}>
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
          </View>

          {/* Bad pub + extra click row */}
          <View style={{ flexDirection: 'row', gap: 6, marginTop: 6, alignItems: 'center', transform: corpFlipped ? [{ rotate: '180deg' }] : [] }}>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={BAD_PUB_ICON}
                value={gs.corp.badPub}
                color={C.badpub}
                flexHeight
                onChange={d => {
                  update(s => ({ ...s, corp: { ...s.corp, badPub: clamp(s.corp.badPub + d, 0, 99) } }));
                  addLog('corp', d > 0 ? 'Bad pub +1' : 'Bad pub −1');
                }}
              />
            </View>
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

        {/* Center Ladder */}
        <CenterLadder
          corpScore={gs.corp.agenda}
          runnerScore={gs.runner.agenda}
          corpColor={corpColor}
          runnerColor={runnerColor}
          onCorpScore={() => {
            update(s => ({
              ...s,
              corp: { ...s.corp, agenda: clamp(s.corp.agenda + 1, 0, 99) },
            }));
            addLog('corp', 'Scored agenda +1');
          }}
          onCorpDec={() => {
            update(s => ({ ...s, corp: { ...s.corp, agenda: clamp(s.corp.agenda - 1, 0, 99) } }));
            addLog('corp', 'Agenda −1');
          }}
          onRunnerScore={() => {
            update(s => ({
              ...s,
              runner: { ...s.runner, agenda: clamp(s.runner.agenda + 1, 0, 99) },
            }));
            addLog('runner', 'Stole agenda +1');
          }}
          onRunnerDec={() => {
            update(s => ({ ...s, runner: { ...s.runner, agenda: clamp(s.runner.agenda - 1, 0, 99) } }));
            addLog('runner', 'Agenda −1');
          }}
        />

        {/* Runner panel */}
        <View style={{
          flex: 1, borderRadius: 10, padding: 8,
          backgroundColor: gs.active === 'runner' ? rgba(runnerColor, 0.06) : theme.panel,
          borderWidth: gs.active === 'runner' ? 2 : 1,
          borderColor: rgba(runnerColor, gs.active === 'runner' ? 0.6 : 0.2),
          opacity: gs.active === 'corp' ? theme.inactiveOpacity : 1,
        }}>
          {/* Header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <View style={{ width: 3, height: 14, borderRadius: 2, backgroundColor: runnerColor, transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }} />
            <View style={{ transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }}>
              <FactionGlyph faction={runnerFaction} size={18} />
            </View>
            <Text style={{
              fontFamily: 'Rajdhani_700Bold', fontSize: 11, letterSpacing: 2, color: runnerColor, flex: 1,
              transform: runnerFlipped ? [{ rotate: '180deg' }] : [],
            }}>
              {runnerFaction?.name || 'RUNNER'}
            </Text>
            <Pressable
              onPressIn={() => setRunnerFlipped(v => !v)}
              style={{
                padding: 3, paddingHorizontal: 6, borderRadius: 5,
                borderWidth: 1,
                borderColor: rgba(runnerColor, runnerFlipped ? 0.5 : 0.2),
                backgroundColor: runnerFlipped ? rgba(runnerColor, 0.12) : 'transparent',
                transform: runnerFlipped ? [{ rotate: '180deg' }] : [],
              }}
            >
              <Text style={{ fontSize: 10, color: rgba(runnerColor, runnerFlipped ? 0.9 : 0.4) }}>⇅</Text>
            </Pressable>
            {gs.active === 'runner' && (
              <View style={{ flexDirection: 'row', gap: 4, transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }}>
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
          <View style={{ flexDirection: 'row', gap: 4, marginBottom: 6, flexWrap: 'wrap' }}>
            {Array.from({ length: 4 + gs.runner.extra }, (_, i) => (
              <View key={i} style={{ transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }}>
                <ClickToken
                  filled={i < gs.runner.clicks}
                  color={runnerColor}
                  onTap={gs.active === 'runner'
                    ? () => handleRunnerTokenTap(i, i < gs.runner.clicks)
                    : undefined}
                  ghost={i >= 4}
                  size={i >= 4 ? 32 : 38}
                  radius={theme.tokenRadius}
                />
              </View>
            ))}
          </View>

          {/* Credits */}
          <View style={{ flex: 1, minHeight: 0, transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }}>
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
          </View>

          {/* Stat chips row + extra click */}
          <View style={{ flexDirection: 'row', gap: 4, marginTop: 6, alignItems: 'center', transform: runnerFlipped ? [{ rotate: '180deg' }] : [] }}>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={TAG_ICON} value={gs.runner.tags} color={C.gold} flexHeight
                onChange={d => {
                  update(s => ({ ...s, runner: { ...s.runner, tags: clamp(s.runner.tags + d, 0, 99) } }));
                  addLog('runner', d > 0 ? 'Tag +1' : 'Tag −1');
                }}
              />
            </View>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={BRAIN_ICON} value={gs.runner.brain} color={C.purple} flexHeight
                onChange={d => {
                  update(s => ({ ...s, runner: { ...s.runner, brain: clamp(s.runner.brain + d, 0, 99) } }));
                  addLog('runner', d > 0 ? 'Core damage +1' : 'Core damage −1');
                }}
              />
            </View>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={HAND_ICON} value={handSize} color={runnerColor} flexHeight
                onChange={d => {
                  update(s => ({ ...s, runner: { ...s.runner, handBonus: clamp(s.runner.handBonus + d, -5, 10) } }));
                  addLog('runner', d > 0 ? 'Hand size +1' : 'Hand size −1');
                }}
              />
            </View>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={MU_ICON} value={gs.runner.mu} color={C.mu} flexHeight
                onChange={d => {
                  update(s => ({ ...s, runner: { ...s.runner, mu: clamp(s.runner.mu + d, 0, 12) } }));
                  addLog('runner', d > 0 ? 'MU +1' : 'MU −1');
                }}
              />
            </View>
            <View style={{ flex: 1, height: 36 }}>
              <StatChip
                iconSource={LINK_ICON} value={gs.runner.link} color={C.link} flexHeight
                onChange={d => {
                  update(s => ({ ...s, runner: { ...s.runner, link: clamp(s.runner.link + d, 0, 99) } }));
                  addLog('runner', d > 0 ? 'Link +1' : 'Link −1');
                }}
              />
            </View>
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
      </View>

      {/* Bottom bar — End Turn */}
      <View style={{ flexShrink: 0 }}>
        <Pressable
          onPressIn={handleEndTurn}
          style={{
            borderRadius: 8, padding: 8,
            alignItems: 'center', justifyContent: 'center',
            flexDirection: 'row', gap: 8,
            backgroundColor: rgba(theme.green, 0.10),
            borderWidth: 1, borderColor: rgba(theme.green, 0.45),
          }}
        >
          <Icon source={CLICK_ICON} size={12} color={theme.green} />
          <Text style={{
            fontSize: 11, fontWeight: '700', letterSpacing: 2.5,
            color: theme.green, fontFamily: 'Rajdhani_700Bold',
          }}>
            END {gs.active === 'corp' ? 'CORP' : 'RUNNER'} TURN
          </Text>
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
