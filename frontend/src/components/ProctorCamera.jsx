import React, { useEffect, useRef, useState } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const ProctorCamera = ({ sessionId, userId }) => {
  const webcamRef = useRef(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(() => {
      captureFrame();
    }, 3000);

    return () => clearInterval(interval);
  }, [sessionId]);

  const captureFrame = async () => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (!imageSrc) return;

    const blob = await fetch(imageSrc).then(res => res.blob());

    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("user_id", userId);
    formData.append("file", blob, "frame.jpg");

    try {
      const res = await axios.post(
        "http://localhost:8004/analyze-frame",
        formData
      );

      setAlerts(res.data.alerts || []);
    } catch (err) {
      console.error("Proctor Error:", err);
    }
  };

  return (
    <div className="mt-6">
      <Webcam
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        width={320}
      />

      {alerts.length > 0 && (
        <div className="mt-3 text-red-500">
          {alerts.map((a, i) => (
            <p key={i}>⚠ {a}</p>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProctorCamera;