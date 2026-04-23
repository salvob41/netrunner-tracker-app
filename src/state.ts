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

export interface GameState {
  round: number;
  active: 'corp' | 'runner';
  corp: CorpState;
  runner: RunnerState;
  log: LogEntry[];
  winner: 'corp' | 'runner' | null;
}

export function makeInitialState(): GameState {
  return {
    round: 1,
    active: 'corp',
    corp:   { clicks:3, extra:0, credits:5, agenda:0, badPub:0 },
    runner: { clicks:4, extra:0, credits:5, agenda:0, tags:0, brain:0, handBonus:0, mu:4, link:0 },
    log: [{ round:0, player:'game', message:'Game started' }],
    winner: null,
  };
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}
