export interface Atmosphere {
  corp: string;
  runner: string;
  bg: string;
  panel: string;
  border: string;
  green: string;
}

export const ATMOSPHERES: Record<string, Atmosphere> = {
  'Neon Punk':    { corp:'#2fb8ff', runner:'#ff5020', bg:'#07090d', panel:'#0d1119', border:'#1a2535', green:'#00f0a0' },
  'Terminal':     { corp:'#00d060', runner:'#d0a000', bg:'#020a03', panel:'#051208', border:'#0a2010', green:'#00ff80' },
  'Midnight':     { corp:'#7070ff', runner:'#ff40c0', bg:'#07060f', panel:'#100e1a', border:'#201838', green:'#40ffb0' },
  'Blood & Void': { corp:'#ff5030', runner:'#c040ff', bg:'#0b0005', panel:'#180010', border:'#300020', green:'#40ffc0' },
};

export const C = {
  gold:   '#ffbe00',
  red:    '#ff1e3a',
  purple: '#b560ff',
  badpub: '#1dbd55',
  mu:     '#20c0e0',
  link:   '#40d080',
  text:   '#ccdae8',
  dim:    '#48606e',
};

export function hex2rgb(hex: string): string {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `${r},${g},${b}`;
}

export function rgba(hex: string, alpha: number): string {
  return `rgba(${hex2rgb(hex)},${alpha})`;
}

export interface Faction {
  id: string;
  name: string;
  short: string;
  color: string;
}

export const CORP_FACTIONS: Faction[] = [
  { id:'hb',      name:'Haas-Bioroid', short:'HB',  color:'#a855f7' },
  { id:'jinteki', name:'Jinteki',      short:'JTK', color:'#ef4444' },
  { id:'nbn',     name:'NBN',          short:'NBN', color:'#f59e0b' },
  { id:'weyland', name:'Weyland',      short:'WEY', color:'#4ade80' },
];

export const RUNNER_FACTIONS: Faction[] = [
  { id:'anarch',   name:'Anarch',   short:'ANA', color:'#ff5020' },
  { id:'criminal', name:'Criminal', short:'CRI', color:'#3b82f6' },
  { id:'shaper',   name:'Shaper',   short:'SHA', color:'#10b981' },
];
