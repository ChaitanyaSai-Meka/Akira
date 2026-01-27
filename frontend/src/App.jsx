import { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = 'ws://localhost:8002/ws';
const SAMPLE_RATE = 16000;

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [llmResponse, setLlmResponse] = useState('');
  const [status, setStatus] = useState('Disconnected');

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    connectWebSocket();
    startListening();

    return () => {
      cleanup();
      if (wsRef.current) wsRef.current.close();
      window.speechSynthesis.cancel();
    };
  }, []);

  const connectWebSocket = () => {
    const ws = new WebSocket(BACKEND_URL);

    ws.onopen = () => {
      setIsConnected(true);
      setStatus('Listening...');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };

    ws.onerror = () => setStatus('Connection Error');
    ws.onclose = () => {
      setIsConnected(false);
      setStatus('Disconnected');
    };

    wsRef.current = ws;
  };

  const handleMessage = (data) => {
    switch (data.type) {
      case 'speech_start':
        setStatus('Listening...');
        setLiveTranscript('');
        setTranscript('');
        setLlmResponse('');
        break;

      case 'live_transcript':
        setLiveTranscript(data.text);
        break;

      case 'transcript':
        setTranscript(data.text);
        setLiveTranscript('');
        setStatus('Thinking...');
        break;

      case 'llm_response':
        setLlmResponse(data.text);
        speakText(data.text);
        break;

      case 'speech_end':
        if (!isSpeaking) setStatus('Listening...');
        break;
    }
  };

  const speakText = (text) => {
    if (!text || !window.speechSynthesis) return;

    setIsSpeaking(true);
    setStatus('Speaking...');
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    utterance.onend = () => {
      setIsSpeaking(false);
      setStatus('Listening...');

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'tts_finished' }));
      }
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
      setStatus('Listening...');

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'tts_finished' }));
      }
    };

    window.speechSynthesis.speak(utterance);
  };

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      streamRef.current = stream;
      audioContextRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      const processor = audioContextRef.current.createScriptProcessor(512, 1, 1);

      processor.onaudioprocess = (e) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const int16Data = new Int16Array(inputData.length);

          for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }

          wsRef.current.send(int16Data.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      processorRef.current = processor;

      setIsListening(true);
    } catch (err) {
      console.error('Microphone error:', err);
      setStatus('Microphone permission denied');
    }
  };

  const cleanup = () => {
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
  };

  return (
    <div className="app">
      <div className="orb-container">
        <div className={`orb ${isListening && !isSpeaking ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
          <div className="orb-core"></div>
          <div className="orb-ring"></div>
          <div className="orb-ring-2"></div>
        </div>
      </div>

      <div className="container">
        <h1>AKIRA</h1>

        <div className={`status-bar ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator"></div>
          <span>{status}</span>
        </div>

        <div className="conversation">
          {liveTranscript && (
            <div className="message live">
              <div className="message-label">LISTENING</div>
              <div className="message-text">{liveTranscript}</div>
            </div>
          )}

          {transcript && (
            <div className="message user">
              <div className="message-label">YOU</div>
              <div className="message-text">{transcript}</div>
            </div>
          )}

          {llmResponse && (
            <div className="message assistant">
              <div className="message-label">AKIRA</div>
              <div className="message-text">{llmResponse}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
