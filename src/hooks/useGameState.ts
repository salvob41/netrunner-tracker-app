import { useState, useEffect, useCallback, useRef } from 'react';
import { Faction, Atmosphere } from '../theme';
import { makeInitialState, clamp, GameState } from '../state';

interface UseGameStateProps {
  corpFaction: Faction;
  runnerFaction: Faction;
  onReset: () => void;
  theme: Atmosphere & { tokenRadius: number; inactiveOpacity: number };
}

export function useGameState({ corpFaction, runnerFaction, onReset, theme }: UseGameStateProps) {
  const [gs, setGs] = useState<GameState>(makeInitialState);
  const [showLog, setShowLog] = useState(false);
  const [corpFlipped, setCorpFlipped] = useState(false);
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

  return {
    gs, setGs, update, addLog,
    showLog, setShowLog,
    corpFlipped, setCorpFlipped,
    runnerFlipped, setRunnerFlipped,
    corpCreditFlush, runnerCreditFlush,
    handleEndTurn, handleCorpTokenTap, handleRunnerTokenTap, handleNewGame,
    corpColor, runnerColor, activeColor, handSize,
    corpFaction, runnerFaction, onReset, theme,
  };
}

export type GameHook = ReturnType<typeof useGameState>;
