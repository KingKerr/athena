'use client';

import { useEffect, useRef, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL;
if (!API_BASE) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
}
const ASK_URL = `${API_BASE}/api/ask`;
const TTS_URL = `${API_BASE}/api/tts`;
const MAX_CHUNKS = 4;
const SOURCE_PREVIEW_LENGTH = 320;
const PRESET_PROMPTS = [
  'What are some risk factors an investor should be aware of?',
  'What competitive pressures are discussed in the filing?',
  'What risks could affect future operating results or stock price?',
];

type Chunk = {
  chunk_id: string;
  ticker: string;
  doc_type: string;
  doc_id: string;
  filing_date: string;
  section_name: string | null;
  chunk_order: number;
  chunk_text: string;
  similarity: number;
};

type RetrievalSummary = {
  ticker: string;
  year: number;
  question: string;
  requested_limit: number;
  returned_chunks: number;
  top_similarity: number;
  doc_types: string[];
};

type AskResponse = {
  answer: string;
  chunks?: Chunk[];
  retrieval_summary?: RetrievalSummary;
};

export default function Page() {
  const [conversationId, setConversationId] = useState('');
  const [ticker, setTicker] = useState('NFLX');
  const [year, setYear] = useState('2025');
  const [question, setQuestion] = useState('What are some risk factors an investor should be aware of?');
  const [answer, setAnswer] = useState('');
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [summary, setSummary] = useState<RetrievalSummary | null>(null);
  const [expandedChunks, setExpandedChunks] = useState<Record<string, boolean>>({});
  const [isAsking, setIsAsking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [error, setError] = useState('');
  const [audioError, setAudioError] = useState('');
  const [audioUrl, setAudioUrl] = useState('');

  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const id =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? crypto.randomUUID()
        : `conv-${Date.now()}`;
    setConversationId(id);
  }, []);

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();

    if (!conversationId) return;

    setIsAsking(true);
    setError('');
    setAudioError('');

    try {
      const payload = {
        conversation_id: conversationId,
        ticker: ticker.trim().toUpperCase(),
        year: Number(year),
        question: question.trim(),
        mode: 'text',
        limit: MAX_CHUNKS,
      };

      const res = await fetch(ASK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const text = await res.text();

      if (!res.ok) {
        throw new Error(`Ask request failed: ${res.status} ${text}`);
      }

      const data: AskResponse = JSON.parse(text);
      const nextChunks = (data.chunks ?? []).slice(0, MAX_CHUNKS);

      setAnswer(data.answer ?? '');
      setChunks(nextChunks);
      setSummary(data.retrieval_summary ?? null);
      setExpandedChunks({});
    } catch (err) {
      setAnswer('');
      setChunks([]);
      setSummary(null);
      setExpandedChunks({});
      setError(err instanceof Error ? err.message : 'Unknown ask error');
    } finally {
      setIsAsking(false);
    }
  }

  async function handleSpeak() {
    if (!answer.trim()) return;

    setIsSpeaking(true);
    setAudioError('');

    try {
      const res = await fetch(TTS_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: answer }),
      });

      if (!res.ok) {
        let message = 'Audio is temporarily unavailable';
        try {
          const errorData = await res.json();
          const detail = 
            typeof errorData?.detail == 'string'
              ? errorData.detail 
              : JSON.stringify(errorData?.detail ?? errorData);
          if (detail.toLowerCase().includes('paid_plan_required')) {
            message = 'Audio is unavailable because the current voice requires a paid ElevenLabs plan.';
          } else if (detail.toLowerCase().includes('voice')) {
            message = 'Audio is unavailable for the current voice configuration.';
          } else if (detail.toLowerCase().includes('api key')) {
            message = 'Audio is unavailable because the ElevenLabs API key is not properly configured.';
          }
         }  catch {
              message = 'Audio is temporarily unavailable.';
            }
            throw new Error(message);
        }

      const blob = await res.blob();

      if (!blob.size) {
        throw new Error('Audio could not be generated for this answer.');
      }

      const nextAudioUrl = URL.createObjectURL(blob);

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }

      setAudioUrl(nextAudioUrl);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = nextAudioUrl;
        audioRef.current.load();
        await audioRef.current.play();
      }
    } catch (err) {
      setAudioError(err instanceof Error ? err.message : 'Unknown TTS error');
    } finally {
      setIsSpeaking(false);
    }
  }

  function formatSimilarity(value: number) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function formatDocType(value: string) {
    return value.
      replaceAll('_', ' ')
      .split(' ')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  function getAnswerSubtitle() {
    if (!summary) return '';
    const chunkCount = Math.min(summary.returned_chunks, MAX_CHUNKS);
    return `Grounded in ${chunkCount} filing excerpt${chunkCount === 1 ? '': 's'}
    from ${summary.ticker} ${summary.year}.`;
  }

  function getSourceText(chunk: Chunk) {
    const isExpanded = expandedChunks[chunk.chunk_id];
    if (isExpanded || chunk.chunk_text.length <= SOURCE_PREVIEW_LENGTH) {
      return chunk.chunk_text;
    }
    return `${chunk.chunk_text.slice(0, SOURCE_PREVIEW_LENGTH).trim()}...`;
  }

  function canExpand(chunk: Chunk) {
    return chunk.chunk_text.length > SOURCE_PREVIEW_LENGTH;
  }

  function toggleChunk(chunkId: string) {
    setExpandedChunks((current) => ({
      ...current,
      [chunkId]: !current[chunkId],
    }));
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div className="heroCopy">
          <div className="eyebrow">Athena</div>
          <h1 className="title">Grounded answers using NFLX 10-Ks</h1>
          <p className="subtitle">
            Ask a question about a recent NFLX filing, retrieve the most relevant supporting passages,
            and play the answer as audio.
          </p>
        </div>
      </section>

      <section className="layout">
        <form className="panel formPanel" onSubmit={handleAsk}>
          <div className="panelHeader">Query</div>

          <label className="label" htmlFor="ticker">
            Ticker
          </label>
          <input
            id="ticker"
            className="input"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="NFLX"
          />

          <label className="label" htmlFor="year">
            Filing year
          </label>
          <select
            id="year"
            className="input"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="2025">2025</option>
            <option value="2026">2026</option>  
          </select>
          <label className="label" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            className="textarea"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={6}
            placeholder="What are some risk factors an investor should be aware of?"
          />
          <div className="promptRow">
            {PRESET_PROMPTS.map((prompt) => {
              const isSelected = question == prompt;
              return (
                <button 
                  key={prompt}
                  type="button"
                  className={`promptChip ${isSelected ? 'promptChipSelected' : ''}`}
                  onClick={() => setQuestion(prompt)}
                >  
                  {prompt}
                </button>  
            );
          })}
          </div>

          <div className="actions">
            <button 
              type="submit" 
              className="button buttonPrimary" 
              disabled={isAsking || !conversationId}
            >
              {isAsking ? 'Retrieving...' : 'Ask'}
            </button>

            <button
              type="button"
              className="button buttonSecondary"
              onClick={handleSpeak}
              disabled={isSpeaking || !answer}
            >
              {isSpeaking ? 'Generating audio...' : 'Play answer'}
            </button>
          </div>

          {error ? <p className="message messageError">{error}</p> : null}
          {audioError ? <p className="message messageError">{audioError}</p> : null}

          <audio ref={audioRef} className="audio" controls preload="none" />

          {summary ? (
            <div className="metaGrid">
              <div className="metaCard">
                <span className="metaLabel">Ticker</span>
                <span className="metaValue">{summary.ticker}</span>
              </div>
              <div className="metaCard">
                <span className="metaLabel">Year used</span>
                <span className="metaValue">{summary.year}</span>
              </div>
              <div className="metaCard">
                <span className="metaLabel">Chunks</span>
                <span className="metaValue">{Math.min(summary.returned_chunks, MAX_CHUNKS)}</span>
              </div>
              <div className="metaCard">
                <span className="metaLabel">Top match</span>
                <span className="metaValue">{formatSimilarity(summary.top_similarity)}</span>
              </div>
            </div>
          ) : null}
        </form>

        <div className="resultsColumn">
          <section className="panel">
            <div className="panelHeader">Answer</div>
             {summary ? <p className="answerSubtitle">{getAnswerSubtitle()}</p> : null}
             {summary?.doc_types?.length ? (
               <div className="badgeRow">
                 {summary.doc_types.map((docType) =>(
                   <span key={docType} className="typeBadge">
                    {formatDocType(docType)}
                   </span>
                 ))} 
               </div>
             ) : null}
            <div className="answerBody">
              {answer || 'Your grounded answer will appear here after you run a query.'}
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">Sources</div>

            {chunks.length ? (
              <div className="sourceList">
                {chunks.slice(0, MAX_CHUNKS).map((chunk) => (
                  <article className="sourceCard" key={chunk.chunk_id}>
                    <div className="sourceMeta">
                      <span>{chunk.doc_type}</span>
                      <span>{chunk.filing_date}</span>
                      <span>{formatSimilarity(chunk.similarity)}</span>
                    </div>

                    {chunk.section_name ? (
                      <div className="sourceSection">{chunk.section_name}</div>
                    ) : null}

                    <p className="sourceText">{getSourceText(chunk)}</p>

                    {canExpand(chunk) ? (
                      <button
                        type="button"
                        className="textButton"
                        onClick={() => toggleChunk(chunk.chunk_id)}
                      >
                        {expandedChunks[chunk.chunk_id] ? 'Show less' : 'Show more'}
                      </button>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="emptyState">
                Supporting filing passages will appear here once a query succeeds.
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}