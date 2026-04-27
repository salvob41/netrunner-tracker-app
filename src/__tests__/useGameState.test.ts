import { renderHook, act } from '@testing-library/react-native';
import { useGameState } from '../hooks/useGameState';

const defaultProps = {
  corpFaction: { id: 'hb', name: 'HB', short: 'HB', color: '#6b2fbf' },
  runnerFaction: { id: 'anarch', name: 'Anarch', short: 'A', color: '#ff5020' },
  onReset: jest.fn(),
  theme: {
    bg: '#07090d', panel: '#101418', corp: '#2fb8ff', runner: '#ff5020',
    green: '#00f0a0', gold: '#f0c030', tokenRadius: 12, inactiveOpacity: 0.72,
  } as any,
};

describe('useGameState', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useGameState(defaultProps));
    const { gs } = result.current;

    expect(gs.round).toBe(1);
    expect(gs.active).toBe('corp');
    expect(gs.corp.clicks).toBe(3);
    expect(gs.corp.credits).toBe(5);
    expect(gs.runner.clicks).toBe(4);
    expect(gs.runner.credits).toBe(5);
    expect(gs.winner).toBeNull();
  });

  it('end turn switches from corp to runner', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => { result.current.handleEndTurn(); });

    expect(result.current.gs.active).toBe('runner');
    expect(result.current.gs.runner.clicks).toBe(4);
    expect(result.current.gs.round).toBe(1); // still round 1
  });

  it('end turn switches from runner to corp and increments round', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    // Corp → Runner
    act(() => { result.current.handleEndTurn(); });
    // Runner → Corp
    act(() => { result.current.handleEndTurn(); });

    expect(result.current.gs.active).toBe('corp');
    expect(result.current.gs.round).toBe(2);
    expect(result.current.gs.corp.clicks).toBe(3);
  });

  it('corp token tap spends a click', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => { result.current.handleCorpTokenTap(0, true); });

    expect(result.current.gs.corp.clicks).toBe(2);
  });

  it('corp token tap on unfilled restores a click', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    // Spend one
    act(() => { result.current.handleCorpTokenTap(0, true); });
    // Restore
    act(() => { result.current.handleCorpTokenTap(2, false); });

    expect(result.current.gs.corp.clicks).toBe(3);
  });

  it('runner token tap does nothing on corp turn', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => { result.current.handleRunnerTokenTap(0, true); });

    expect(result.current.gs.runner.clicks).toBe(4); // unchanged
  });

  it('update applies state changes', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => {
      result.current.update(s => ({ ...s, corp: { ...s.corp, credits: 10 } }));
    });

    expect(result.current.gs.corp.credits).toBe(10);
  });

  it('addLog appends to game log', () => {
    const { result } = renderHook(() => useGameState(defaultProps));
    const initialLength = result.current.gs.log.length;

    act(() => { result.current.addLog('corp', 'Test action'); });

    expect(result.current.gs.log.length).toBe(initialLength + 1);
    expect(result.current.gs.log[result.current.gs.log.length - 1].message).toBe('Test action');
  });

  it('triggers corp win at 7 agenda', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => {
      result.current.update(s => ({ ...s, corp: { ...s.corp, agenda: 7 } }));
    });

    expect(result.current.gs.winner).toBe('corp');
  });

  it('triggers runner win at 7 agenda', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => {
      result.current.update(s => ({ ...s, runner: { ...s.runner, agenda: 7 } }));
    });

    expect(result.current.gs.winner).toBe('runner');
  });

  it('handleReset resets game state and calls onReset', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    // Change some state
    act(() => {
      result.current.update(s => ({ ...s, corp: { ...s.corp, credits: 20 }, round: 5 }));
    });
    expect(result.current.gs.corp.credits).toBe(20);

    act(() => { result.current.handleReset(); });

    expect(result.current.gs.corp.credits).toBe(5);
    expect(result.current.gs.round).toBe(1);
    expect(defaultProps.onReset).toHaveBeenCalled();
  });

  it('handleNewGame resets state and calls onReset', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => {
      result.current.update(s => ({ ...s, runner: { ...s.runner, tags: 3 } }));
    });

    act(() => { result.current.handleNewGame(); });

    expect(result.current.gs.runner.tags).toBe(0);
    expect(defaultProps.onReset).toHaveBeenCalled();
  });

  it('extra clicks cycle correctly for corp', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    // Simulate the extra click button cycling
    act(() => {
      result.current.update(s => {
        const next = (s.corp.extra + 1) % 4;
        return { ...s, corp: { ...s.corp, extra: next, clicks: s.corp.clicks + 1 } };
      });
    });

    expect(result.current.gs.corp.extra).toBe(1);
    expect(result.current.gs.corp.clicks).toBe(4);
  });

  it('activeColor matches the current turn', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    expect(result.current.activeColor).toBe(defaultProps.corpFaction.color);

    act(() => { result.current.handleEndTurn(); });

    expect(result.current.activeColor).toBe(defaultProps.runnerFaction.color);
  });

  it('handSize accounts for brain damage', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    expect(result.current.handSize).toBe(5); // base

    act(() => {
      result.current.update(s => ({ ...s, runner: { ...s.runner, brain: 2 } }));
    });

    expect(result.current.handSize).toBe(3); // 5 - 2
  });

  it('handSize accounts for handBonus', () => {
    const { result } = renderHook(() => useGameState(defaultProps));

    act(() => {
      result.current.update(s => ({ ...s, runner: { ...s.runner, handBonus: 2 } }));
    });

    expect(result.current.handSize).toBe(7); // 5 + 2
  });
});
