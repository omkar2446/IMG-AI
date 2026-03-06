import React, { useEffect, useMemo, useState } from "react";
import PromptForm from "./components/PromptForm";
import ImageGallery from "./components/ImageGallery";
import LoaderOverlay from "./components/LoaderOverlay";
import { fetchHistory, generateImage } from "./services/api";

function toDataUrl(base64) {
  return `data:image/png;base64,${base64}`;
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [size, setSize] = useState(1024);
  const [numImages, setNumImages] = useState(1);
  const [inputImage, setInputImage] = useState("");
  const [strength, setStrength] = useState(0.55);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentBatch, setCurrentBatch] = useState([]);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  const allImages = useMemo(() => [...currentBatch, ...history], [currentBatch, history]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const data = await fetchHistory();
        setHistory(data.items || []);
      } catch {
      }
    };

    loadHistory();
  }, []);

  const onFieldChange = (field, value) => {
    if (field === "prompt") setPrompt(value);
    if (field === "negativePrompt") setNegativePrompt(value);
    if (field === "size") setSize(value);
    if (field === "numImages") setNumImages(value);
    if (field === "inputImage") setInputImage(value);
    if (field === "strength") setStrength(value);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsGenerating(true);

    try {
      const payload = {
        prompt,
        negative_prompt: negativePrompt,
        image_size: size,
        num_images: numImages,
        input_image: inputImage || null,
        strength
      };

      const res = await generateImage(payload);
      const now = new Date().toISOString();
      const batch = (res.images || []).map((base64, idx) => ({
        id: `${Date.now()}-${idx}`,
        dataUrl: toDataUrl(base64),
        prompt,
        createdAt: now
      }));

      setCurrentBatch(batch);

      const updated = await fetchHistory().catch(() => ({ items: [] }));
      setHistory(updated.items || []);
    } catch (err) {
      setError(err.message || "Generation failed");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <main className="app-gradient min-h-screen">
      <LoaderOverlay visible={isGenerating} />

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-50 sm:text-4xl">SDXL Studio</h1>
          <p className="mt-2 text-slate-400">Generate high-quality images via Stable Diffusion XL running locally.</p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
          <div>
            <PromptForm
              prompt={prompt}
              negativePrompt={negativePrompt}
              size={size}
              numImages={numImages}
              inputImage={inputImage}
              strength={strength}
              isGenerating={isGenerating}
              onChange={onFieldChange}
              onSubmit={onSubmit}
            />
            {error && <p className="mt-3 rounded-lg border border-red-800 bg-red-950/70 p-3 text-sm text-red-200">{error}</p>}
          </div>

          <ImageGallery items={allImages} title="Generated Images" />
        </div>
      </div>
    </main>
  );
}

