'use client';

import { useState } from 'react';
import { apiClient } from '@/lib/api';

export default function TestAudioAIPage() {
  const [mediaUrl, setMediaUrl] = useState('https://www2.cs.uic.edu/~i101/SoundFiles/StarWars60.wav');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'process' | 'transcribe'>('transcribe');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = { media_url: mediaUrl };
      const response =
        mode === 'process'
          ? await apiClient.audioProcess(payload)
          : await apiClient.audioTranscribe(payload);
      setResult(response);
    } catch (err: any) {
      setError(err?.message ?? 'Request failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-semibold">Audio AI Test</h1>

        <form onSubmit={onSubmit} className="space-y-4 bg-gray-900 p-4 rounded-lg border border-white/10">
          <div>
            <label htmlFor="mediaUrl" className="block text-sm mb-2">Media URL</label>
            <input
              id="mediaUrl"
              type="text"
              value={mediaUrl}
              onChange={(e) => setMediaUrl(e.target.value)}
              placeholder="http(s)://..., file://..., or /path/to/file.mp3"
              className="w-full px-3 py-2 rounded-md bg-white/10 border border-white/20 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="mode"
                checked={mode === 'transcribe'}
                onChange={() => setMode('transcribe')}
              />
              Transcribe (faster)
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="mode"
                checked={mode === 'process'}
                onChange={() => setMode('process')}
              />
              Full Process (analysis)
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Submitting…' : 'Submit'}
          </button>
        </form>

        {error && (
          <div className="bg-red-900/40 border border-red-700 text-red-200 p-3 rounded">{error}</div>
        )}

        {result && (
          <div className="bg-gray-900 p-4 rounded-lg border border-white/10 overflow-auto">
            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}

        <div className="text-sm text-white/60">
          Gateway: http://localhost:3001 → /audio-ai/api/v1/audio/{mode}
        </div>
      </div>
    </div>
  );
}
