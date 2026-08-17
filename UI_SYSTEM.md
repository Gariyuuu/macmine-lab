# MacMine Lab — UI System

Next.js + TypeScript + Tailwind + shadcn/ui (`frontend/src/components/ui/`
holds the primitives). No separate design-token/theming doc exists and
none was reconstructed here — this project's UI conventions weren't
formalized in a spec anywhere found during this pass; infer them from the
existing components rather than inventing a system that was never
written down. [Needs confirmation] whether a design-system doc exists
elsewhere (e.g., in the showcase site's own styling) that this pass
missed.

Known real UI facts:
- Honest-degradation is a UI convention, not just a backend one: pages
  show "Unavailable"/"not enough data" states rather than a loading
  spinner masking missing data indefinitely (README, multiple sections).
- The dashboard never shows a "MINING" state or XMR/USD figures outside
  of real mining mode — benchmark mode is explicitly labeled as such.
