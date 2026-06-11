import { useState, useEffect, useCallback, useRef } from 'react';
import * as Haptics from 'expo-haptics';
import { Faction, Atmosphere } from '../theme';
import { makeInitialState, clamp, GameState, Mark, MIN_WIN_TARGET, MAX_WIN_TARGET } from '../state';

interface UseGameStateProps {
  corpFaction: Faction;
  runnerFaction: Faction;
  onReset: () => void;
  theme: Atmosphere & { tokenRadius: number; inactiveOpacity: number };
}

export function useGameState({ corpFaction, runnerFaction, onReset, theme }: UseGameStateProps) {
  const [gs, setGs] = useState<GameState>(makeInitialState);
  const [showLog, setShowLog] = useState(false);
  const [showDice, setShowDice] = useState(false);
  const [showWinTarget, setShowWinTarget] = useState(false);
  const [corpFlipped, setCorpFlipped] = useState(true);
  const [runnerFlipped, setRunnerFlipped] = useState(false);

  // Flush refs for credit counters — called before any turn transition.
  const corpCreditFlush = useRef<() => void>(() => {});
  const runnerCreditFlush = useRef<() => void>(() => {});

  const update = (fn: (s: GameState) => GameState) => setGs(prev => fn(prev));

  // Stable log appender — avoids re-creating closures in child handlers
  const addLog = useCallback((player: 'corp' | 'runner' | 'game', message: string) => {
    setGs(prev => ({
      ...prev,
      log: [...prev.log, { round: prev.round, player, message }],
    }));
  }, []);

  /**
   * Apply a net delta to a clamped numeric stat and log "Label ±n → result",
   * so the log shows both the change and the value it landed on. Used by the
   * batched chips/ladders (tags, bad pub, agenda, etc.).
   */
  const adjustStat = useCallback((
    player: 'corp' | 'runner',
    field: string,
    d: number,
    pos: string,
    neg: string,
    lo: number = 0,
    hi: number = 99,
  ) => {
    setGs(prev => {
      const side = prev[player] as unknown as Record<string, number>;
      const next = clamp(side[field] + d, lo, hi);
      const verb = d > 0 ? `${pos} +${d}` : `${neg} −${Math.abs(d)}`;
      return {
        ...prev,
        [player]: { ...side, [field]: next },
        log: [...prev.log, { round: prev.round, player, message: `${verb} → ${next}` }],
      } as GameState;
    });
  }, []);

  // Check win condition after each agenda change
  useEffect(() => {
    if (gs.winner) return;
    const corpWin = gs.corp.agenda >= gs.winTarget;
    const runnerWin = gs.runner.agenda >= gs.winTarget;
    if (!corpWin && !runnerWin) {
      // Both sides back below 7 → re-arm so a future win still triggers.
      if (gs.winDismissed) update(s => ({ ...s, winDismissed: false }));
      return;
    }
    if (gs.winDismissed) return; // player chose "Keep Playing" past this win
    if (corpWin) update(s => ({ ...s, winner: 'corp' }));
    else if (runnerWin) update(s => ({ ...s, winner: 'runner' }));
  }, [gs.corp.agenda, gs.runner.agenda, gs.winner, gs.winDismissed, gs.winTarget]);

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
        const markWasSet = s.mark !== null;
        return {
          ...s,
          round: nextRound,
          active: 'corp',
          runner: { ...s.runner, extra: 0 },
          corp: { ...s.corp, clicks: 3 + s.corp.extra },
          mark: null,
          log: [...s.log, {
            round: s.round, player: 'game',
            message: `Round ${s.round} complete · Round ${nextRound} begins${markWasSet ? ' · Mark cleared' : ''}`,
          }],
        };
      }
    });
  };

  /** Roll a generic die (1..sides). Logs and vibrates briefly. Returns the result. */
  const rollDie = useCallback((sides: number): number => {
    const result = 1 + Math.floor(Math.random() * sides);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    setGs(prev => ({
      ...prev,
      log: [...prev.log, { round: prev.round, player: 'game', message: `Rolled d${sides}: ${result}` }],
    }));
    return result;
  }, []);

  /** Roll the marked central (d3 → HQ/R&D/Archives), set mark, log. Returns the central. */
  const rollMark = useCallback((): Mark => {
    const centrals: Mark[] = ['HQ', 'R&D', 'Archives'];
    const result = centrals[Math.floor(Math.random() * 3)];
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    setGs(prev => ({
      ...prev,
      mark: result,
      log: [...prev.log, { round: prev.round, player: 'game', message: `Mark: ${result}` }],
    }));
    return result;
  }, []);

  /** Set the agenda-to-win target to an absolute value (from the picker modal).
   *  Clamped to [MIN_WIN_TARGET, MAX_WIN_TARGET]. */
  const setWinTarget = useCallback((value: number) => {
    setGs(prev => {
      const next = clamp(value, MIN_WIN_TARGET, MAX_WIN_TARGET);
      if (next === prev.winTarget) return prev;
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
      return {
        ...prev,
        winTarget: next,
        log: [...prev.log, { round: prev.round, player: 'game', message: `Agenda to win: ${next}` }],
      };
    });
  }, []);

  /** Manually set the mark (no roll). Logs and replaces any existing mark. */
  const setMark = useCallback((m: Mark) => {
    setGs(prev => ({
      ...prev,
      mark: m,
      log: [...prev.log, { round: prev.round, player: 'game', message: `Mark set: ${m}` }],
    }));
  }, []);

  /** Clear the mark manually. Logs only if a mark was set. */
  const clearMark = useCallback(() => {
    setGs(prev => prev.mark === null ? prev : {
      ...prev,
      mark: null,
      log: [...prev.log, { round: prev.round, player: 'game', message: 'Mark cleared' }],
    });
  }, []);

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

  /** Dismiss the win overlay and resume the current game (e.g. after a
   *  mis-tap to 7). Suppresses the auto-win until agenda drops below 7 again. */
  const handleKeepPlaying = () => {
    update(s => ({
      ...s,
      winner: null,
      winDismissed: true,
      log: [...s.log, { round: s.round, player: 'game', message: 'Game continued' }],
    }));
  };

  const handleReset = () => {
    corpCreditFlush.current();
    runnerCreditFlush.current();
    setGs(makeInitialState());
    onReset();
  };

  return {
    gs, setGs, update, addLog, adjustStat,
    showLog, setShowLog,
    showDice, setShowDice,
    showWinTarget, setShowWinTarget,
    corpFlipped, setCorpFlipped,
    runnerFlipped, setRunnerFlipped,
    corpCreditFlush, runnerCreditFlush,
    handleEndTurn, handleCorpTokenTap, handleRunnerTokenTap, handleNewGame, handleReset, handleKeepPlaying,
    rollDie, rollMark, setMark, clearMark, setWinTarget,
    corpColor, runnerColor, activeColor, handSize,
    corpFaction, runnerFaction, onReset, theme,
  };
}

export type GameHook = ReturnType<typeof useGameState>;
