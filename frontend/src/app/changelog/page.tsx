import fs from "node:fs";
import path from "node:path";
import Link from "next/link";
import { MarkdownContent } from "@/lib/markdown";

function readChangelog(): string {
  try {
    const filePath = path.join(process.cwd(), "..", "CHANGELOG.md");
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "# Changelog\n\nCHANGELOG.md could not be read from this build — see the repo directly.";
  }
}

export default function ChangelogPage() {
  const content = readChangelog();

  return (
    <div className="flex min-h-screen flex-col bg-zinc-950 text-zinc-100">
      <header className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-lg font-semibold tracking-tight">MacMine Lab</span>
          <span className="text-xs text-zinc-500">Changelog</span>
        </div>
        <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-200">
          ← Dashboard
        </Link>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-8">
        <div>
          <h1 className="text-xl font-semibold">Changelog</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Every phase, what shipped, and what was actually verified before it did — rendered
            straight from the repo&apos;s <code className="rounded bg-white/10 px-1 py-0.5 text-xs">CHANGELOG.md</code>.
          </p>
        </div>

        <MarkdownContent content={content} />
      </main>
    </div>
  );
}
