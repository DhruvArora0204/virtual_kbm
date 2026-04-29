import { useEffect, useState, useRef } from 'react'
import './App.css'

const KEYBOARD_LAYOUT = [
  ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
  ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
  ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'BACKSPACE'],
  ['SPACE']
];

function App() {
  const [wsState, setWsState] = useState({
    mode: 'mouse',
    cursor_x: 0,
    cursor_y: 0,
    click: false,
    frame: ''
  });
  
  const [inputText, setInputText] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const clickTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const keysRef = useRef<{ [key: string]: HTMLDivElement | null }>({});
  const keyboardContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const connectWs = () => {
      const ws = new WebSocket('ws://localhost:8765');
      
      ws.onopen = () => console.log('Connected to Python Backend');
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setWsState(prev => {
          // Detect click transition
          if (data.click && !prev.click && data.mode === 'keyboard') {
            handleVirtualClick(data.cursor_x, data.cursor_y);
          }
          return data;
        });
      };

      ws.onclose = () => {
        console.log('Disconnected. Reconnecting...');
        setTimeout(connectWs, 1000);
      };

      wsRef.current = ws;
    };

    connectWs();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleVirtualClick = (x_norm: number, y_norm: number) => {
    if (clickTimeoutRef.current) return;
    
    clickTimeoutRef.current = setTimeout(() => {
      clickTimeoutRef.current = null;
    }, 500); // debounce
    
    // Convert normalized coordinates back to actual screen coordinates.
    const screenX = x_norm * window.innerWidth;
    const screenY = y_norm * window.innerHeight;
    
    // Find the element exactly under the virtual cursor and click it!
    const elements = document.elementsFromPoint(screenX, screenY);
    for (const el of elements) {
      if (el instanceof HTMLElement && (el.classList.contains('key') || el.classList.contains('mode-card') || el.classList.contains('clear-btn'))) {
        el.click();
        
        // Visual feedback
        el.classList.add('active-key');
        setTimeout(() => el.classList.remove('active-key'), 200);
        break;
      }
    }
  };

  const handleKeyPress = (key: string) => {
    if (key === 'BACKSPACE') {
      setInputText(prev => prev.slice(0, -1));
    } else if (key === 'SPACE') {
      setInputText(prev => prev + ' ');
    } else {
      setInputText(prev => prev + key);
    }
  };

  const toggleMode = (newMode: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ mode: newMode }));
    }
  };

  return (
    <div className="dashboard">
      {/* Sidebar / Control Panel */}
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon"></div>
          <h1>GestureOps</h1>
        </div>

        <div className="status-panel">
          <h3>SYSTEM STATUS</h3>
          <div className="status-item">
            <span className={`status-dot ${wsRef.current?.readyState === 1 ? 'connected' : 'disconnected'}`}></span>
            {wsRef.current?.readyState === 1 ? 'Backend Connected' : 'Waiting for Backend...'}
          </div>
        </div>

        <div className="mode-panel">
          <h3>CURRENT MODE</h3>
          <div 
            className={`mode-card ${wsState.mode === 'mouse' ? 'active-mode' : ''}`}
            onClick={() => toggleMode('mouse')}
            style={{ cursor: 'pointer' }}
          >
            <div className="mode-icon">🖱️</div>
            <div className="mode-text">
              <h4>Mouse Mode</h4>
              <p>Control OS Cursor</p>
            </div>
          </div>
          <div 
            className={`mode-card ${wsState.mode === 'keyboard' ? 'active-mode' : ''}`}
            onClick={() => toggleMode('keyboard')}
            style={{ cursor: 'pointer' }}
          >
            <div className="mode-icon">⌨️</div>
            <div className="mode-text">
              <h4>Keyboard Mode</h4>
              <p>Virtual Typing</p>
            </div>
          </div>
        </div>

        <div className="camera-panel">
          <h3>CAMERA FEED</h3>
          <div className="video-feed">
            {wsState.frame ? (
              <img src={`data:image/jpeg;base64,${wsState.frame}`} alt="Video Feed" />
            ) : (
              <div className="video-placeholder">No Signal</div>
            )}
            <div className="feed-overlay"></div>
          </div>
        </div>
        
        <div className="instructions">
          <h4>Gestures:</h4>
          <ul>
            <li><strong>Move Cursor:</strong> Index Finger</li>
            <li><strong>Click/Type:</strong> Pinch Thumb & Index</li>
            <li><strong>Toggle Mode:</strong> Click Mode Cards</li>
          </ul>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="main-content">
        <div className="header">
          <h2>Virtual Workspace</h2>
          <div className="user-profile"></div>
        </div>

        <div className="workspace">
          <div className="input-box">
            <div className="input-text">
              {inputText || <span className="placeholder">Start typing with gestures...</span>}
              <span className="cursor-blink">|</span>
            </div>
            <button className="clear-btn" onClick={() => setInputText('')}>Clear</button>
          </div>

          <div className={`keyboard-container ${wsState.mode !== 'keyboard' ? 'disabled' : ''}`} ref={keyboardContainerRef}>
            {wsState.mode !== 'keyboard' && (
              <div className="keyboard-overlay-message">
                Switch to Keyboard Mode to type
              </div>
            )}
            <div className="keyboard">
              {KEYBOARD_LAYOUT.map((row, rowIdx) => (
                <div key={rowIdx} className="keyboard-row">
                  {row.map((key) => (
                    <div
                      key={key}
                      ref={el => keysRef.current[key] = el}
                      className={`key ${key === 'SPACE' ? 'key-space' : ''} ${key === 'BACKSPACE' ? 'key-backspace' : ''}`}
                      onClick={() => handleKeyPress(key)}
                    >
                      {key}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Virtual Cursor Overlay (Absolute to Window) */}
      {wsState.mode === 'keyboard' && (
        <div 
          className={`virtual-cursor ${wsState.click ? 'clicking' : ''}`}
          style={{
            left: `${wsState.cursor_x * 100}vw`,
            top: `${wsState.cursor_y * 100}vh`
          }}
        >
          <div className="cursor-ring"></div>
        </div>
      )}
    </div>
  )
}

export default App
