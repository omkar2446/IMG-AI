import React from "react";

const SIZES = [512, 768, 1024];
const COUNTS = [1, 2, 3, 4];

export default function PromptForm({
  prompt,
  negativePrompt,
  size,
  numImages,
  inputImage,
  strength,
  isGenerating,
  onChange,
  onSubmit
}) {
  const onInputImageChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      onChange("inputImage", "");
      return;
    }

    if (!file.type.startsWith("image/")) {
      onChange("inputImage", "");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      onChange("inputImage", typeof reader.result === "string" ? reader.result : "");
    };
    reader.readAsDataURL(file);
  };

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-2xl border border-slate-700/70 bg-slate-900/70 p-5 shadow-glow backdrop-blur"
    >
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-slate-300">Prompt</label>
        <textarea
          value={prompt}
          onChange={(e) => onChange("prompt", e.target.value)}
          className="h-28 w-full rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400"
          placeholder="A cinematic portrait of an astronaut walking through neon rain in Tokyo"
          required
        />
      </div>

      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-slate-300">Negative Prompt</label>
        <textarea
          value={negativePrompt}
          onChange={(e) => onChange("negativePrompt", e.target.value)}
          className="h-20 w-full rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400"
          placeholder="blurry, distorted, low quality"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Image Size</label>
          <select
            value={size}
            onChange={(e) => onChange("size", Number(e.target.value))}
            className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400"
          >
            {SIZES.map((s) => (
              <option key={s} value={s}>{`${s} x ${s}`}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Number of Images</label>
          <select
            value={numImages}
            onChange={(e) => onChange("numImages", Number(e.target.value))}
            className="w-full rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-slate-100 outline-none focus:border-cyan-400"
          >
            {COUNTS.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="mt-4">
        <label className="mb-2 block text-sm font-medium text-slate-300">Input Photo (Optional)</label>
        <input
          type="file"
          accept="image/*"
          onChange={onInputImageChange}
          className="w-full cursor-pointer rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-300 file:mr-4 file:cursor-pointer file:rounded-md file:border-0 file:bg-cyan-500 file:px-3 file:py-1.5 file:text-sm file:font-semibold file:text-slate-950 hover:file:bg-cyan-400"
        />
        {inputImage && (
          <div className="mt-3 rounded-xl border border-slate-700 bg-slate-800/70 p-3">
            <img src={inputImage} alt="Input preview" className="max-h-48 w-full rounded-lg object-contain" />
            <button
              type="button"
              onClick={() => onChange("inputImage", "")}
              className="mt-2 rounded-md border border-slate-600 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500 hover:text-slate-100"
            >
              Remove Photo
            </button>
          </div>
        )}
      </div>

      <div className="mt-4">
        <div className="mb-2 flex items-center justify-between">
          <label className="block text-sm font-medium text-slate-300">Transformation Strength</label>
          <span className="text-xs text-slate-400">{strength.toFixed(2)}</span>
        </div>
        <input
          type="range"
          min="0.1"
          max="0.95"
          step="0.05"
          value={strength}
          onChange={(e) => onChange("strength", Number(e.target.value))}
          className="w-full accent-cyan-400"
          disabled={!inputImage}
        />
        <p className="mt-1 text-xs text-slate-400">
          {inputImage ? "Higher values make stronger edits to your uploaded photo." : "Upload a photo to enable img2img strength control."}
        </p>
      </div>

      <button
        type="submit"
        disabled={isGenerating}
        className="mt-5 w-full rounded-xl bg-cyan-500 px-4 py-2.5 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:bg-cyan-700"
      >
        {isGenerating ? "Generating..." : "Generate"}
      </button>
    </form>
  );
}
