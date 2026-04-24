import { useCallback, useEffect, useRef, useState } from 'react';

export const BATCH_MS = 800;

export function useBatchedDelta(
  commit: (delta: number) => void,
  windowMs: number = BATCH_MS,
) {
  const [pending, setPending] = useState(0);
  const pendingRef = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flush = useCallback(() => {
    if (timer.current) { clearTimeout(timer.current); timer.current = null; }
    const d = pendingRef.current;
    if (d !== 0) {
      commit(d);
      pendingRef.current = 0;
      setPending(0);
    }
  }, [commit]);

  const bump = useCallback((delta: number) => {
    pendingRef.current += delta;
    setPending(pendingRef.current);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(flush, windowMs);
  }, [flush, windowMs]);

  // Flush on unmount so in-flight deltas aren't lost.
  useEffect(() => () => flush(), [flush]);

  return { pending, bump, flush };
}
