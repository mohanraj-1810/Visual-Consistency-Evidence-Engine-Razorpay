import React, { useState, useEffect } from 'react';

export default function AnalysisCounter({ startTs, endTs, loading, visible }) {
  const [elapsed, setElapsed] = useState('00:00s');

  useEffect(() => {
    if (!startTs) {
      setElapsed('00:00s');
      return;
    }

    const calcElapsed = (toTs) => {
      const diffMs = Math.max(0, toTs - startTs);
      const totalSec = Math.floor(diffMs / 1000);
      const mins = String(Math.floor(totalSec / 60)).padStart(2, '0');
      const secs = String(totalSec % 60).padStart(2, '0');
      return `${mins}:${secs}s`;
    };

    if (!loading || endTs) {
      // Analysis complete: freeze timer immediately at completion timestamp
      const freezeTime = endTs || Date.now();
      setElapsed(calcElapsed(freezeTime));
      return;
    }

    // While running: tick live timer
    const updateTimer = () => {
      setElapsed(calcElapsed(Date.now()));
    };

    updateTimer();
    const interval = setInterval(updateTimer, 100);
    return () => clearInterval(interval);
  }, [startTs, endTs, loading]);

  return (
    <div
      className={`analysis-counter ${visible ? 'visible' : ''}`}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className="eyebrow">{loading ? 'Analysis Duration' : 'Total Duration'}</span>
      <span className="counter-value">{elapsed}</span>
    </div>
  );
}
