// src/hooks/useVoiceChat.js

import { useState, useRef, useCallback, useEffect } from 'react';
import { playAudioBlob } from '../utils/audioUtils';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const RECORDING_TIMEOUT = 8000; // auto-send after 8 seconds max
const SILENCE_DURATION = 3000;  // 3 seconds silence to auto-send

export const STATES = {
  IDLE: 'idle',
  LISTENING: 'listening',
  THINKING: 'thinking',
  SPEAKING: 'speaking',
  ERROR: 'error',
};

export function useVoiceChat() {
  const [status, setStatus] = useState(STATES.IDLE);
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState('');
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState(() => {
    // Load from localStorage if available
    return localStorage.getItem('selectedVoice') || '';
  });

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const isRecordingRef = useRef(false);
  const isSessionActiveRef = useRef(false);
  const silenceTimerRef = useRef(null);
  const maxTimerRef = useRef(null);
  const lastSpeechTimeRef = useRef(null);
  const hasSpeechRef = useRef(false);

  useEffect(() => {
    initSession();
    return () => cleanup();
  }, []);

  async function initSession() {
    try {
      const res = await fetch(`${API_BASE}/session`);
      const data = await res.json();
      setSessionId(data.session_id);
    } catch (e) {
      console.error('Session init failed:', e);
    }
  }

  function cleanup() {
    clearTimers();
    stopStream();
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  }

  function clearTimers() {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
  }

  function stopStream() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }

  // ── VAD using AnalyserNode ────────────────────────────────────────────────
  function startVAD(stream) {
    try {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 512;
      analyserRef.current.smoothingTimeConstant = 0.3;

      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);

      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);

      hasSpeechRef.current = false;
      lastSpeechTimeRef.current = Date.now();

      function tick() {
        if (!isRecordingRef.current) return;

        // Use frequency data (byte) — more reliable than time domain
        analyserRef.current.getByteFrequencyData(dataArray);

        // Average volume across frequency bins
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;

        // avg > 10 means there is sound (speech)
        if (avg > 10) {
          hasSpeechRef.current = true;
          lastSpeechTimeRef.current = Date.now();

          // Reset silence timer on every speech frame
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        } else if (hasSpeechRef.current && !silenceTimerRef.current) {
          // Silence after speech — start countdown
          silenceTimerRef.current = setTimeout(() => {
            if (isRecordingRef.current) {
              console.log('Silence detected — sending...');
              stopAndSend();
            }
          }, SILENCE_DURATION);
        }

        animationFrameRef.current = requestAnimationFrame(tick);
      }

      tick();
    } catch (e) {
      console.error('VAD error:', e);
    }
  }

  // ── Start recording ───────────────────────────────────────────────────────
  const startRecording = useCallback(async () => {
    if (isRecordingRef.current) return;

    try {
      setError(null);
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100);

      isRecordingRef.current = true;
      setStatus(STATES.LISTENING);

      // Start VAD
      startVAD(stream);

      // Safety max timer — auto send after 8s no matter what
      maxTimerRef.current = setTimeout(() => {
        if (isRecordingRef.current) {
          console.log('Max timer reached — sending...');
          stopAndSend();
        }
      }, RECORDING_TIMEOUT);

    } catch (e) {
      console.error('Mic error:', e);
      setError('Microphone access denied. Please allow microphone access.');
      setStatus(STATES.ERROR);
      isSessionActiveRef.current = false;
      setIsSessionActive(false);
    }
  }, []);

  // ── Stop recording ────────────────────────────────────────────────────────
  const stopRecording = useCallback(() => {
    isRecordingRef.current = false;
    clearTimers();

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    stopStream();

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    setStatus(STATES.IDLE);
  }, []);

  // ── Stop and send ─────────────────────────────────────────────────────────
  const stopAndSend = useCallback(async () => {
    if (!isRecordingRef.current) return;

    isRecordingRef.current = false;
    clearTimers();

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    stopStream();

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Wait for final chunks
    await new Promise((r) => setTimeout(r, 300));

    const chunks = audioChunksRef.current;

    if (!chunks.length || !hasSpeechRef.current) {
      console.log('No speech detected, stopping...');
      setStatus(STATES.IDLE);
      isSessionActiveRef.current = false;
      setIsSessionActive(false);
      return;
    }

    const audioBlob = new Blob(chunks, { type: 'audio/webm' });
    await sendAudio(audioBlob);
  }, [sessionId]);

  // ── Send audio ────────────────────────────────────────────────────────────
  async function sendAudio(audioBlob) {
    setStatus(STATES.THINKING);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'audio.webm');

      const params = new URLSearchParams({
        session_id: sessionId || '',
        ...(selectedVoice && { voice_id: selectedVoice }),
      });

      const res = await fetch(
        `${API_BASE}/voice?${params}`,
        { method: 'POST', body: formData }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Request failed');
      }

      const userText = decodeURIComponent(res.headers.get('X-User-Text') || '');
      const aiText = decodeURIComponent(res.headers.get('X-AI-Text') || '');
      const newSessionId = res.headers.get('X-Session-Id');

      if (newSessionId && !sessionId) setSessionId(newSessionId);

      if (userText) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now(), role: 'user', content: userText },
        ]);
      }
      if (aiText) {
        setMessages((prev) => [
          ...prev,
          { id: Date.now() + 1, role: 'assistant', content: aiText },
        ]);
      }

      setStatus(STATES.SPEAKING);
      const audioResponseBlob = await res.blob();
      await playAudioBlob(audioResponseBlob);

      // Don't restart recording — wait for user to click button again
      setStatus(STATES.IDLE);

    } catch (e) {
      console.error('Send audio failed:', e);
      setError(e.message || 'Something went wrong');
      setStatus(STATES.ERROR);
      isSessionActiveRef.current = false;
      setIsSessionActive(false);
    }
  }

  // ── Send text ─────────────────────────────────────────────────────────────
  const sendTextMessage = useCallback(async (text) => {
    if (!text.trim()) return;
    setInputText('');
    setStatus(STATES.THINKING);

    if (isRecordingRef.current) stopRecording();

    const userMessageId = Date.now();
    const aiMessageId = Date.now() + 1;

    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: 'user', content: text },
    ]);

    try {
      // Add streaming assistant message
      setMessages((prev) => [
        ...prev,
        { id: aiMessageId, role: 'assistant', content: '', isStreaming: true },
      ]);

      const res = await fetch(`${API_BASE}/chat-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, session_id: sessionId || '' }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Request failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines[lines.length - 1];

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.chunk) {
              fullText += data.chunk;
              // Update the message with streamed content
              setMessages((prev) => 
                prev.map((msg) =>
                  msg.id === aiMessageId
                    ? { ...msg, content: fullText }
                    : msg
                )
              );
            }
            if (data.done) {
              // Mark streaming as complete
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === aiMessageId
                    ? { ...msg, isStreaming: false }
                    : msg
                )
              );
            }
          }
        }
      }

      // Convert response to speech
      setStatus(STATES.SPEAKING);
      const ttsRes = await fetch(`${API_BASE}/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: fullText,
          ...(selectedVoice && { voice_id: selectedVoice }),
        }),
      });

      if (ttsRes.ok) {
        const audioBlob = await ttsRes.blob();
        await playAudioBlob(audioBlob);
      }

      // Don't restart recording — wait for user to click button again
      setStatus(STATES.IDLE);
    } catch (e) {
      console.error('Send text failed:', e);
      setError(e.message || 'Something went wrong');
      setStatus(STATES.ERROR);
      
      // Remove streaming indicator
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMessageId
            ? { ...msg, isStreaming: false }
            : msg
        )
      );
    }
  }, [sessionId, selectedVoice]);

  // ── Toggle session ────────────────────────────────────────────────────────
  const toggleSession = useCallback(() => {
    if (status === STATES.THINKING || status === STATES.SPEAKING) return;

    if (isSessionActiveRef.current) {
      isSessionActiveRef.current = false;
      setIsSessionActive(false);
      stopRecording();
    } else {
      isSessionActiveRef.current = true;
      setIsSessionActive(true);
      startRecording();
    }
  }, [status, startRecording, stopRecording]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    if (sessionId) {
      fetch(`${API_BASE}/session/${sessionId}`, { method: 'DELETE' });
    }
    initSession();
  }, [sessionId]);

  const handleVoiceChange = useCallback((voiceId) => {
    setSelectedVoice(voiceId);
    localStorage.setItem('selectedVoice', voiceId);
  }, []);

  return {
    status,
    messages,
    sessionId,
    error,
    isSessionActive,
    inputText,
    setInputText,
    selectedVoice,
    setSelectedVoice: handleVoiceChange,
    toggleSession,
    sendTextMessage,
    clearMessages,
  };
}