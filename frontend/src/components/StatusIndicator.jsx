// src/components/StatusIndicator.jsx

import { STATES } from '../hooks/useVoiceChat';
import './StatusIndicator.css';

export default function StatusIndicator({ status }) {
  const config = {
    [STATES.IDLE]: { label: 'Ready to chat', color: 'idle' },
    [STATES.LISTENING]: { label: 'Listening...', color: 'listening' },
    [STATES.THINKING]: { label: 'Generating response...', color: 'thinking' },
    [STATES.SPEAKING]: { label: 'Playing response...', color: 'speaking' },
    [STATES.ERROR]: { label: 'Error occurred', color: 'error' },
  };

  const { label, color } = config[status] || config[STATES.IDLE];

  return (
    <div className={`status-indicator status-${color}`}>
      <span className="status-dot" />
      <span className="status-label">{label}</span>
    </div>
  );
}