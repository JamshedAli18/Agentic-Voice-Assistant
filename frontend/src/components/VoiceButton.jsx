// src/components/VoiceButton.jsx

import { STATES } from '../hooks/useVoiceChat';
import './VoiceButton.css';

export default function VoiceButton({ status, isSessionActive, onClick }) {
  const isBusy = status === STATES.THINKING || status === STATES.SPEAKING;

  function getIcon() {
    if (isBusy) {
      return '⟳';
    }
    if (isSessionActive) {
      return '■';
    }
    return '●';
  }

  return (
    <button
      className={`voice-button ${isSessionActive ? 'voice-button--active' : ''} voice-button--${status}`}
      onClick={onClick}
      disabled={isBusy}
      aria-label={isSessionActive ? 'Stop session' : 'Start voice session'}
    >
      {isSessionActive && <span className="voice-button__ring" />}
      {isSessionActive && <span className="voice-button__ring voice-button__ring--delay" />}
      <span className="voice-button__icon">{getIcon()}</span>
    </button>
  );
}