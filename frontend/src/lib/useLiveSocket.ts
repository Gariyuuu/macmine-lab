"use client";

import { useEffect, useRef, useState } from "react";
import { WS_BASE, type LiveWsPayload } from "./api";

export type ConnectionState = "connecting" | "open" | "closed";

/**
 * Subscribes to the backend's /ws/live stream (real telemetry + miner +
 * benchmark state, pushed once a second). Reconnects with backoff if the
 * backend isn't up yet or drops — this is a local dev tool, so the backend
 * frequently isn't running when the frontend is.
 *
 * `onPayload` fires synchronously inside the real WebSocket `onmessage`
 * callback (not a useEffect reacting to state) — that's the correct place
 * for callers to derive additional state from each tick, e.g. accumulating
 * chart points, without triggering cascading-render lint warnings.
 */
export function useLiveSocket(onPayload?: (payload: LiveWsPayload) => void) {
  const [payload, setPayload] = useState<LiveWsPayload | null>(null);
  const [state, setState] = useState<ConnectionState>("connecting");
  const retryDelay = useRef(1000);
  const onPayloadRef = useRef(onPayload);
  useEffect(() => {
    onPayloadRef.current = onPayload;
  });

  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (cancelled) return;
      setState("connecting");
      ws = new WebSocket(`${WS_BASE}/ws/live`);

      ws.onopen = () => {
        retryDelay.current = 1000;
        setState("open");
      };
      ws.onmessage = (event) => {
        try {
          const parsed: LiveWsPayload = JSON.parse(event.data);
          setPayload(parsed);
          onPayloadRef.current?.(parsed);
        } catch {
          // ignore malformed frames rather than crash the UI
        }
      };
      ws.onclose = () => {
        setState("closed");
        if (cancelled) return;
        retryTimer = setTimeout(connect, retryDelay.current);
        retryDelay.current = Math.min(retryDelay.current * 2, 15000);
      };
      ws.onerror = () => {
        ws?.close();
      };
    }

    connect();
    return () => {
      cancelled = true;
      if (retryTimer) clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);

  return { payload, state };
}
