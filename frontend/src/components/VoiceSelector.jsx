// src/components/VoiceSelector.jsx

import { useEffect, useState } from 'react';
import './VoiceSelector.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function VoiceSelector({ selectedVoice, onVoiceChange }) {
  const [voices, setVoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVoices();
  }, []);

  async function fetchVoices() {
    try {
      const res = await fetch(`${API_BASE}/voices`);
      if (res.ok) {
        const data = await res.json();
        setVoices(data.voices || []);
      }
    } catch (error) {
      console.error('Failed to fetch voices:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="voice-selector">
        <label className="voice-label">Voice</label>
        <select className="voice-select" disabled>
          <option>Loading voices...</option>
        </select>
      </div>
    );
  }

  return (
    <div className="voice-selector">
      <label className="voice-label">Voice</label>
      <select
        className="voice-select"
        value={selectedVoice || ''}
        onChange={(e) => onVoiceChange(e.target.value)}
      >
        <option value="">Default Voice</option>
        {voices.map((voice) => (
          <option key={voice.id} value={voice.id}>
            {voice.name}
          </option>
        ))}
      </select>
    </div>
  );
}
