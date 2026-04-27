import { renderHook, act } from '@testing-library/react-native';
import { useBatchedDelta, BATCH_MS } from '../hooks/useBatchedDelta';

beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('useBatchedDelta', () => {
  it('starts with pending = 0', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));
    expect(result.current.pending).toBe(0);
  });

  it('accumulates bumps into pending', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(1); });
    expect(result.current.pending).toBe(1);

    act(() => { result.current.bump(1); });
    expect(result.current.pending).toBe(2);

    act(() => { result.current.bump(-1); });
    expect(result.current.pending).toBe(1);
  });

  it('does not call commit until timer fires', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(1); });
    expect(commit).not.toHaveBeenCalled();
  });

  it('commits net delta after window elapses', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(1); });
    act(() => { result.current.bump(1); });
    act(() => { result.current.bump(-1); });

    act(() => { jest.advanceTimersByTime(BATCH_MS); });

    expect(commit).toHaveBeenCalledTimes(1);
    expect(commit).toHaveBeenCalledWith(1); // net: +1+1-1 = 1
    expect(result.current.pending).toBe(0);
  });

  it('resets timer on each bump', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(1); });
    act(() => { jest.advanceTimersByTime(BATCH_MS - 100); });
    expect(commit).not.toHaveBeenCalled();

    // Another bump resets the window
    act(() => { result.current.bump(1); });
    act(() => { jest.advanceTimersByTime(BATCH_MS - 100); });
    expect(commit).not.toHaveBeenCalled();

    act(() => { jest.advanceTimersByTime(100); });
    expect(commit).toHaveBeenCalledWith(2);
  });

  it('flush() commits immediately and clears pending', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(3); });
    act(() => { result.current.flush(); });

    expect(commit).toHaveBeenCalledWith(3);
    expect(result.current.pending).toBe(0);
  });

  it('flush() is a no-op when pending is 0', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.flush(); });
    expect(commit).not.toHaveBeenCalled();
  });

  it('uses latest commit callback via ref (no stale closure)', () => {
    const commit1 = jest.fn();
    const commit2 = jest.fn();

    const { result, rerender } = renderHook(
      ({ commit }: { commit: (d: number) => void }) => useBatchedDelta(commit),
      { initialProps: { commit: commit1 as (d: number) => void } },
    );

    act(() => { result.current.bump(1); });

    // Parent re-renders with new commit callback
    rerender({ commit: commit2 });

    // Timer fires — should use commit2, not commit1
    act(() => { jest.advanceTimersByTime(BATCH_MS); });

    expect(commit1).not.toHaveBeenCalled();
    expect(commit2).toHaveBeenCalledWith(1);
  });

  it('flushes on unmount', () => {
    const commit = jest.fn();
    const { result, unmount } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(2); });
    unmount();

    expect(commit).toHaveBeenCalledWith(2);
  });

  it('does not double-commit after flush + timer', () => {
    const commit = jest.fn();
    const { result } = renderHook(() => useBatchedDelta(commit));

    act(() => { result.current.bump(1); });
    act(() => { result.current.flush(); });

    // Timer would have fired here, but flush already committed
    act(() => { jest.advanceTimersByTime(BATCH_MS); });

    expect(commit).toHaveBeenCalledTimes(1);
  });
});
