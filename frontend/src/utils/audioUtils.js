// src/utils/audioUtils.js

export const SILENCE_THRESHOLD = 0.02;  // higher = less sensitive
export const SILENCE_DURATION = 3000;   // 3 seconds of silence to auto-send
export const MIN_SPEECH_DURATION = 1000; // must speak for at least 1 second

export function getRMS(buffer) {
  let sum = 0;
  for (let i = 0; i < buffer.length; i++) {
    sum += buffer[i] * buffer[i];
  }
  return Math.sqrt(sum / buffer.length);
}

export async function playAudioBlob(blob) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const arrayBuffer = await blob.arrayBuffer();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start(0);
  return new Promise((resolve) => {
    source.onended = () => {
      audioContext.close();
      resolve();
    };
  });
}