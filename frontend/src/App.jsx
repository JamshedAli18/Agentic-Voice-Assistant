// src/App.jsx

import { useRef } from 'react';
import { useVoiceChat, STATES } from './hooks/useVoiceChat';
import ChatHistory from './components/ChatHistory';
import VoiceButton from './components/VoiceButton';
import StatusIndicator from './components/StatusIndicator';
import VoiceSelector from './components/VoiceSelector';
import './App.css';

export default function App() {
  const {
    status,
    messages,
    error,
    isSessionActive,
    inputText,
    setInputText,
    selectedVoice,
    setSelectedVoice,
    toggleSession,
    sendTextMessage,
    clearMessages,
  } = useVoiceChat();

  const inputRef = useRef(null);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextMessage(inputText);
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="app-header__inner">
          <div className="app-header__title">
            <span className="app-header__dot" />
            <h1>Voice AI</h1>
          </div>
          {messages.length > 0 && (
            <button
              className="app-header__clear"
              onClick={clearMessages}
              aria-label="Clear chat"
            >
              <span>Clear Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Chat area */}
      <main className="app-main">
        <ChatHistory messages={messages} status={status} />
      </main>

      {/* Error */}
      {error && (
        <div className="app-error">
          {error}
        </div>
      )}

      {/* Footer */}
      <footer className="app-footer">
        <div className="app-footer__inner">

          {/* Voice selector */}
          <VoiceSelector 
            selectedVoice={selectedVoice}
            onVoiceChange={setSelectedVoice}
          />

          {/* Status */}
          <StatusIndicator status={status} isSessionActive={isSessionActive} />

          {/* Text input row */}
          <div className="app-input-row">
            <div className="app-input-wrapper">
              <textarea
                ref={inputRef}
                className="app-input"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message or press the mic to speak..."
                rows={1}
                disabled={status === STATES.THINKING || status === STATES.SPEAKING}
              />
              <button
                className="app-send-btn"
                onClick={() => sendTextMessage(inputText)}
                disabled={!inputText.trim() || status === STATES.THINKING || status === STATES.SPEAKING}
                aria-label="Send message"
              >
                ↑
              </button>
            </div>

            {/* Mic button */}
            <VoiceButton
              status={status}
              isSessionActive={isSessionActive}
              onClick={toggleSession}
            />
          </div>

        </div>
      </footer>
    </div>
  );
}