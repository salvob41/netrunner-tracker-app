export interface LogEntry {
  round: number;
  player: 'corp' | 'runner' | 'game';
  message: string;
}

export interface CorpState {
  clicks: number;
  extra: number;
  credits: number;
  agenda: number;
  badPub: number;
}

export interface RunnerState {
  clicks: number;
  extra: number;
  credits: number;
  agenda: number;
  tags: number;
  brain: number;
  handBonus: number;
  mu: number;
  link: number;
}

export type Mark = 'HQ' | 'R&D' | 'Archives';

export interface GameState {
  round: number;
  active: 'corp' | 'runner';
  corp: CorpState;
  runner: RunnerState;
  log: LogEntry[];
  winner: 'corp' | 'runner' | null;
  /** True once the player dismissed a win via "Keep Playing"; suppresses the
   *  auto-win until both agendas drop back below the win target (then re-arms). */
  winDismissed: boolean;
  /** Agenda points required to win (default 7; adjustable from the center ladder). */
  winTarget: number;
  mark: Mark | null;
}

export const MIN_WIN_TARGET = 1;
export const MAX_WIN_TARGET = 10;
export const DEFAULT_WIN_TARGET = 7;

export function makeInitialState(): GameState {
  return {
    round: 1,
    active: 'corp',
    corp:   { clicks:3, extra:0, credits:5, agenda:0, badPub:0 },
    runner: { clicks:4, extra:0, credits:5, agenda:0, tags:0, brain:0, handBonus:0, mu:4, link:0 },
    log: [{ round:0, player:'game', message:'Game started' }],
    winner: null,
    winDismissed: false,
    winTarget: DEFAULT_WIN_TARGET,
    mark: null,
  };
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}
