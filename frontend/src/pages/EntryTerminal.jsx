import React, { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import './EntryTerminal.css';
import { dataURItoBlob } from '../utils/imageUtils';

const EntryTerminal = () => {
  const webcamRef = useRef(null);
  const [status, setStatus] = useState('idle');           // 'idle', 'processing', 'granted', 'denied'
  const [errorMessage, setErrorMessage] = useState('');   // To store backend messages
  const [currentTime, setCurrentTime] = useState(new Date());

  // Clock Logic
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Timer Logic (Auto-scan every 3s)
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
    if (!webcamRef.current || !webcamRef.current.video || webcamRef.current.video.readyState !== 4) return;
    if (status !== 'idle') return;

    setStatus('processing');
    setErrorMessage(''); // Reset previous errors

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

      switch (response.status) {
        case 200:
          // Access Granted
          setStatus('granted');
          break;

        case 403:
          // Permission Denied (Show Reason)
          setStatus('denied');
          setErrorMessage(data.message || "Permission Denied");
          break;

        case 500:
          // Server Error (Show Reason, Do not enter)
          setStatus('denied'); 
          setErrorMessage(data.message || "System Error");
          break;

        case 400:
          // Malformed (e.g., No QR/Face found). 
          setStatus('idle');
          return;
        
        default:
          setStatus('denied');
          setErrorMessage("Unknown Error");
      }

    } catch (error) {
      console.error("Network Error:", error);
      setStatus('denied');
      setErrorMessage("Network connection failed");
    }

    setTimeout(() => {
      setStatus('idle');
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

      {status === 'idle' && <div className="scan-zone"></div>}

      <div className="status-box">
        {status === 'idle' && <p>Hello, please<br/>verify Your QR<br/>code above</p>}
        {status === 'processing' && <p>Verifying...<br/>Please wait</p>}
        
        {status === 'granted' && (
          <p style={{ color: '#4ade80' }}>Access<br/>Granted</p>
        )}
        
        {status === 'denied' && (
          <div>
            <p style={{ color: '#f87171' }}>Access<br/>Denied</p>
            {/* Display the backend error message here */}
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