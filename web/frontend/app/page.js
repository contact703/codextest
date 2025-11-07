'use client';

import { useCallback, useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState(null);
  const [url, setUrl] = useState('');
  const [progress, setProgress] = useState(0);
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault();
      setLoading(true);
      try {
        const formData = new FormData();
        if (file) {
          formData.append('file', file);
        }
        if (url) {
          formData.append('url', url);
        }
        const response = await axios.post(`${API_URL}/jobs`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (event) => {
            if (event.total) {
              setProgress(Math.round((event.loaded / event.total) * 100));
            }
          },
        });
        setJob(response.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    },
    [file, url]
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-8 p-6">
      <header>
        <h1 className="text-3xl font-semibold">Audiodescrição Toolkit</h1>
        <p className="text-slate-300">
          Gere audiodescrição em PT-BR para vídeos locais ou URLs do YouTube/Vimeo.
        </p>
      </header>
      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex h-32 cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-slate-700 bg-slate-950/60 px-6 text-center text-slate-300">
            <span className="text-lg font-medium">Arraste e solte o vídeo aqui</span>
            <span className="text-xs">Formatos suportados: MP4, MOV, AVI</span>
            <input
              type="file"
              accept="video/mp4,video/quicktime,video/x-msvideo"
              className="hidden"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <div className="flex flex-col gap-2">
            <label htmlFor="url" className="text-sm uppercase tracking-wide text-slate-400">
              URL (YouTube/Vimeo)
            </label>
            <input
              id="url"
              type="url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="rounded border border-slate-700 bg-slate-950/60 p-3 text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded bg-sky-500 px-4 py-3 text-sm font-semibold uppercase tracking-wider text-white transition hover:bg-sky-400 disabled:bg-slate-700"
          >
            {loading ? 'Processando...' : 'Gerar Audiodescrição'}
          </button>
          {loading && (
            <div className="flex flex-col gap-2">
              <span className="text-xs uppercase text-slate-400">Enviando arquivo</span>
              <div className="h-2 w-full overflow-hidden rounded bg-slate-800">
                <div className="h-full bg-sky-500" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}
        </form>
      </section>
      {job && (
        <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-6">
          <h2 className="text-xl font-semibold">Resultado</h2>
          <p className="text-sm text-slate-300">Job ID: {job.id}</p>
          <ul className="mt-4 grid gap-2 md:grid-cols-2">
            {job.assets.map((asset) => (
              <li key={asset}>
                <a
                  href={`${API_URL}/jobs/${job.id}/download?path=${encodeURIComponent(asset)}`}
                  className="inline-flex w-full items-center justify-between rounded border border-slate-700 bg-slate-950/50 px-3 py-2 text-sm text-sky-400 hover:border-sky-500"
                >
                  <span>{asset.split('/').pop()}</span>
                  <span className="text-xs uppercase">Download</span>
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
