import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function SeedPhraseWarning() {
  return (
    <Alert className="border-red-500/30 bg-red-500/10">
      <AlertTitle className="text-red-400">
        Never enter your seed phrase or private keys into MacMine Lab.
      </AlertTitle>
      <AlertDescription className="text-red-300/80">
        MacMine Lab only ever needs your public receiving address — the one you share to receive
        payments. It never asks for, stores, or transmits a seed phrase, recovery phrase, private
        key, or spend key. If anything ever asks you for one of those here, stop and don&apos;t
        enter it.
      </AlertDescription>
    </Alert>
  );
}
