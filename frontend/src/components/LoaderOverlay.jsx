import React from "react";

export default function LoaderOverlay({ visible }) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm">
      <div className="rounded-2xl border border-slate-700 bg-slate-900 p-8 text-center shadow-glow">
        <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-slate-700 border-t-cyan-400" />
        <p className="animate-pulseSlow text-sm text-slate-300">Generating with local SDXL...</p>
      </div>
    </div>
  );
}
