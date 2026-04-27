import { clamp, makeInitialState } from '../state';

describe('clamp', () => {
  it('returns value when within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('clamps to minimum', () => {
    expect(clamp(-3, 0, 99)).toBe(0);
  });

  it('clamps to maximum', () => {
    expect(clamp(150, 0, 99)).toBe(99);
  });

  it('handles equal bounds', () => {
    expect(clamp(5, 3, 3)).toBe(3);
  });
});

describe('makeInitialState', () => {
  it('creates corp with 3 clicks and 5 credits', () => {
    const gs = makeInitialState();
    expect(gs.corp.clicks).toBe(3);
    expect(gs.corp.credits).toBe(5);
    expect(gs.corp.agenda).toBe(0);
    expect(gs.corp.badPub).toBe(0);
  });

  it('creates runner with 4 clicks and 5 credits', () => {
    const gs = makeInitialState();
    expect(gs.runner.clicks).toBe(4);
    expect(gs.runner.credits).toBe(5);
    expect(gs.runner.agenda).toBe(0);
    expect(gs.runner.tags).toBe(0);
    expect(gs.runner.brain).toBe(0);
    expect(gs.runner.mu).toBe(4);
    expect(gs.runner.link).toBe(0);
  });

  it('starts on round 1 with corp active', () => {
    const gs = makeInitialState();
    expect(gs.round).toBe(1);
    expect(gs.active).toBe('corp');
    expect(gs.winner).toBeNull();
  });

  it('has initial log entry', () => {
    const gs = makeInitialState();
    expect(gs.log).toHaveLength(1);
    expect(gs.log[0].message).toBe('Game started');
  });
});
