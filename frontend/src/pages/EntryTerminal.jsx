import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import './EntryTerminal.css';
import { dataURItoBlob } from '../utils/imageUtils';

const EntryTerminal = () => {
  const webcamRef = useRef(null);
  const [status, setStatus] = useState('idle');           // 'idle', 'processing', 'granted', 'denied'
  const [errorMessage, setErrorMessage] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const scanLock = useRef(false);
  const timerRef = useRef(null);

  // Clock Logic
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Timer Logic (Auto-scan every 0.5s)
  useEffect(() => {
    let interval;
    if (status === 'idle') {
      interval = setInterval(() => {
        handleScan();
      }, 500);
    }
    return () => clearInterval(interval);
  }, [status]);

  const formatTime = (date) => {
    const pad = (n) => n.toString().padStart(2, '0');
    return `${pad(date.getHours())}:${pad(date.getMinutes())}-${pad(date.getDate())}.${pad(date.getMonth() + 1)}.${date.getFullYear().toString().slice(-2)}`;
  };

  const handleScan = async () => {
    if (!webcamRef.current?.video?.readyState === 4 || scanLock.current) return;

    scanLock.current = true;
    timerRef.current = setTimeout(() => {
        setStatus('processing');
        setErrorMessage('');
    }, 400);

    try {
      const imageSrc = webcamRef.current.getScreenshot();
      const blob = dataURItoBlob(imageSrc);
      const formData = new FormData();
      formData.append('file', blob, 'scan.jpg');

      const response = await fetch('/api/skan', {
        method: 'POST',
        body: formData, 
      });
      const data = await response.json();

      if (timerRef.current) {
          clearTimeout(timerRef.current);
          timerRef.current = null;
      }

      if (response.status === 400) {
          setStatus('idle');
          scanLock.current = false;
          return;
      }

      const responseMap = {
          200: { status: 'granted', message: '' },
          403: { status: 'denied', message: data.message || "No access" },
          500: { status: 'denied', message: data.message || "System Error" }
      };

      const result = responseMap[response.status] || { 
          status: 'denied', 
          message: "Unknown error" 
      };

      setStatus(result.status);
      if (result.message) setErrorMessage(result.message);

    } catch (error) {
      console.error("Network Error:", error);
      if (timerRef.current) clearTimeout(timerRef.current);
      setStatus('denied');
        setErrorMessage("Connection error");
    }
    setTimeout(() => {
        setStatus('idle');
        setErrorMessage('');
        scanLock.current = false;
    }, 3000);
  };

  return (
    <div className="terminal-container">
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        className="webcam-video"
      />
      <div className="scanlines"></div>

      <div className="header-bar">
        <div className="rec-badge"><div className="red-dot"></div> REC</div>
        <div className="timestamp">{formatTime(currentTime)}</div>
      </div>

      <div className="scan-zone"></div>

      <div className="status-box">
        {status === 'idle' && <p>Hello, please<br/>verify Your QR<br/>code above</p>}
        {status === 'processing' && <p>Verifying...<br/>Please wait</p>}
        
        {status === 'granted' && (
          <p style={{ color: '#4ade80' }}>Access<br/>Granted</p>
        )}
        
        {status === 'denied' && (
          <div>
            <p style={{ color: '#f87171' }}>Access<br/>Denied</p>
            <p style={{ fontSize: '1rem', marginTop: '10px', color: '#fff' }}>
              {errorMessage}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EntryTerminal;