import React, { useState, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import ProctorCamera from "../components/ProctorCamera";
const WS_URL = "ws://localhost:8003/ws/interview";

const InterviewRoom = () => {
  const { analysis_id } = useParams();

  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState("connecting");

  const wsRef = useRef(null);
  const recognitionRef = useRef(null);
  const sessionIdRef = useRef(null);

  const silenceTimer = useRef(null);
  const isSpeakingRef = useRef(false);

  //  INIT
  useEffect(() => {
    initSession();
    setupSpeech();

    return () => {
      wsRef.current?.close();
      recognitionRef.current?.stop();
      window.speechSynthesis.cancel();
    };
  }, []);

  // START SESSION
  const initSession = async () => {
    try {
      const res = await fetch("http://localhost:8003/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: 1,
          resume_id: Number(analysis_id),
        }),
      });

      const data = await res.json();

      if (!data.session_id) {
        console.error("Session failed", data);
        return;
      }

      sessionIdRef.current = data.session_id;

      connectWebSocket(data.session_id);

      addMessage("ai", data.question);
      speak(data.question);

    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  // 🔌 WebSocket
  const connectWebSocket = (sessionId) => {
    if (!sessionId) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_URL}/${sessionId}`);

    ws.onopen = () => setStatus("connected");

    ws.onmessage = (event) => {
      const msg = event.data;
      addMessage("ai", msg);
      speak(msg);
    };

    ws.onerror = () => setStatus("error");

    ws.onclose = () => {
      setStatus("disconnected");
    };

    wsRef.current = ws;
  };

  // 🧠 ADD MESSAGE
  const addMessage = (role, content) => {
    setMessages((prev) => [...prev, { role, content }]);
  };

  // 🎤 SPEECH SETUP
  const setupSpeech = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech Recognition not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    let finalTranscript = "";

    recognition.onresult = (event) => {
      let interim = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript + " ";
        } else {
          interim += transcript;
        }
      }

      resetSilenceTimer(finalTranscript.trim());
    };

    recognition.onerror = (e) => {
      console.error("Speech error:", e);
    };

    recognition.onend = () => {
      if (!isSpeakingRef.current) {
        recognition.start(); // auto restart
      }
    };

    recognitionRef.current = recognition;
  };

  // ⏱ SILENCE DETECTION (KEY FEATURE)
  const resetSilenceTimer = (text) => {
    if (silenceTimer.current) {
      clearTimeout(silenceTimer.current);
    }

    silenceTimer.current = setTimeout(() => {
      if (text) {
        sendAnswer(text);
      }
    }, 2000); // 2 sec silence = done speaking
  };

  // 📤 SEND ANSWER
  const sendAnswer = (text) => {
    if (!wsRef.current) return;

    addMessage("user", text);
    wsRef.current.send(text);
  };

  // 🔊 SPEAK LIKE HUMAN
  const speak = (text) => {
    isSpeakingRef.current = true;

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onend = () => {
      isSpeakingRef.current = false;
      startListening();
    };

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  };

  // 🎤 START LISTENING AUTOMATICALLY
  const startListening = () => {
    try {
      recognitionRef.current?.start();
    } catch (e) {}
  };

  return (
    <div className="p-6 text-white bg-black min-h-screen">
      <h1 className="text-xl mb-4">AI Interview</h1>

      <p>Status: {status}</p>

      <div className="mt-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i}>
            <b>{m.role === "ai" ? "AI:" : "You:"}</b> {m.content}
          </div>
        ))}
      </div>

      <p className="mt-6 text-green-400">
        🎤 Speak naturally... no need to click anything
      </p>
    </div>
  );
};

export default InterviewRoom;