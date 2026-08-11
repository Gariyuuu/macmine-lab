"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { api } from "@/lib/api";

const POLL_MS = 2000;

function lineClass(line: string): string {
  const l = line.toLowerCase();
  if (l.includes("error") || l.includes("failed")) return "text-red-400";
  if (l.includes("warn")) return "text-amber-400";
  if (l.includes("ready") || l.includes("accepted")) return "text-emerald-400";
  if (l.includes("bench") || l.includes("speed") || l.includes("randomx")) return "text-cyan-400";
  return "text-zinc-400";
}

export function LogTerminal({ active }: { active: boolean }) {
  const [logFile, setLogFile] = useState<string | null>(null);
  const [lines, setLines] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const data = await api.latestLog(300);
        if (!cancelled) {
          setLogFile(data.log_file);
          setLines(data.lines);
        }
      } catch {
        // backend not reachable yet — leave existing lines in place
      }
    }
    poll();
    const interval = active ? setInterval(poll, POLL_MS) : undefined;
    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
    };
  }, [active]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [lines]);

  return (
    <Card className="border-white/[0.08] bg-zinc-900/70 shadow-xl shadow-black/30">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm font-medium text-zinc-400">Raw XMRig Log</CardTitle>
        <span className="font-mono text-[11px] text-zinc-600">{logFile ?? "no log yet"}</span>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64 rounded-md border border-white/5 bg-black/40 p-3">
          {lines.length === 0 ? (
            <p className="text-xs text-zinc-600">
              Nothing has run yet — start a benchmark to see real XMRig output here.
            </p>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
              {lines.map((line, i) => (
                <div key={i} className={lineClass(line)}>
                  {line}
                </div>
              ))}
              <div ref={bottomRef} />
            </pre>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
