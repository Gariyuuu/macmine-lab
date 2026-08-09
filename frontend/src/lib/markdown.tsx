// Minimal, dependency-free renderer for MacMine Lab's own CHANGELOG.md —
// handles exactly the markdown subset the changelog actually uses
// (h1/h2, paragraphs, wrapped bullet lists, **bold**, `code`, [links](url)).
// No dangerouslySetInnerHTML — everything becomes real React elements.

import React from "react";

type Block =
  | { type: "h1"; text: string }
  | { type: "h2"; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] };

function parseBlocks(md: string): Block[] {
  const lines = md.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (line.trim() === "") {
      i++;
      continue;
    }
    if (line.startsWith("# ")) {
      blocks.push({ type: "h1", text: line.slice(2).trim() });
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      blocks.push({ type: "h2", text: line.slice(3).trim() });
      i++;
      continue;
    }
    if (line.trimStart().startsWith("- ")) {
      const items: string[] = [];
      while (i < lines.length) {
        const current = lines[i];
        if (current.trimStart().startsWith("- ")) {
          items.push(current.trimStart().slice(2).trim());
          i++;
        } else if (current.startsWith("  ") && current.trim() !== "") {
          // Wrapped continuation of the previous bullet.
          items[items.length - 1] += " " + current.trim();
          i++;
        } else {
          break;
        }
      }
      blocks.push({ type: "ul", items });
      continue;
    }
    // Paragraph: accumulate wrapped lines until a blank line or new block.
    let para = line.trim();
    i++;
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("#") &&
      !lines[i].trimStart().startsWith("- ")
    ) {
      para += " " + lines[i].trim();
      i++;
    }
    blocks.push({ type: "p", text: para });
  }

  return blocks;
}

const INLINE_PATTERN = /(\*\*(.+?)\*\*)|(`(.+?)`)|(\[(.+?)\]\((.+?)\))/;

function parseInline(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    const match = INLINE_PATTERN.exec(remaining);
    if (!match || match.index === undefined) {
      nodes.push(remaining);
      break;
    }
    if (match.index > 0) {
      nodes.push(remaining.slice(0, match.index));
    }
    if (match[1]) {
      nodes.push(<strong key={`${keyPrefix}-${key++}`}>{match[2]}</strong>);
    } else if (match[3]) {
      nodes.push(
        <code key={`${keyPrefix}-${key++}`} className="rounded bg-white/10 px-1 py-0.5 text-xs">
          {match[4]}
        </code>
      );
    } else if (match[5]) {
      nodes.push(
        <a
          key={`${keyPrefix}-${key++}`}
          href={match[7]}
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-zinc-300"
        >
          {match[6]}
        </a>
      );
    }
    remaining = remaining.slice(match.index + match[0].length);
  }

  return nodes;
}

export function MarkdownContent({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return (
    <div className="flex flex-col gap-3">
      {blocks.map((block, idx) => {
        const key = `b-${idx}`;
        switch (block.type) {
          case "h1":
            return null; // the page renders its own <h1> title
          case "h2":
            return (
              <h2 key={key} className="mt-8 text-lg font-semibold text-zinc-100 first:mt-0">
                {parseInline(block.text, key)}
              </h2>
            );
          case "ul":
            return (
              <ul key={key} className="ml-5 list-disc space-y-1.5 text-sm text-zinc-400">
                {block.items.map((item, i2) => (
                  <li key={`${key}-${i2}`}>{parseInline(item, `${key}-${i2}`)}</li>
                ))}
              </ul>
            );
          case "p":
            return (
              <p key={key} className="text-sm text-zinc-400">
                {parseInline(block.text, key)}
              </p>
            );
        }
      })}
    </div>
  );
}
