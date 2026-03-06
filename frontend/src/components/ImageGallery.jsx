import React from "react";

function downloadFromDataUrl(dataUrl, filename) {
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = filename;
  a.click();
}

export default function ImageGallery({ items, title }) {
  return (
    <section className="rounded-2xl border border-slate-700/70 bg-slate-900/70 p-5 backdrop-blur">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
        <p className="text-sm text-slate-400">{items.length} image(s)</p>
      </div>

      {items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-700 p-8 text-center text-slate-400">
          Images will appear here after generation.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((img) => (
            <article key={img.id} className="overflow-hidden rounded-xl border border-slate-700 bg-slate-800/80">
              <img src={img.dataUrl || img.url} alt={img.prompt || "Generated image"} className="h-auto w-full" />
              <div className="space-y-2 p-3">
                {img.prompt && (
                  <p className="line-clamp-2 text-xs text-slate-300" title={img.prompt}>
                    {img.prompt}
                  </p>
                )}
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>{new Date(img.createdAt).toLocaleString()}</span>
                  <button
                    onClick={() => downloadFromDataUrl(img.dataUrl || img.url, `${img.id}.png`)}
                    className="rounded-md bg-cyan-500 px-2.5 py-1.5 font-medium text-slate-950 hover:bg-cyan-400"
                  >
                    Download
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
