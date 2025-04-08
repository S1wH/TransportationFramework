// App.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import TransportSolver from './TransportSolver';
import Register from './Register';
import Login from './Login';
import PreviousTables from './PreviousTables';
import { useState } from 'react';
import './App.css';

function App() {
  const [userId, setUserId] = useState<string | null>(localStorage.getItem('userId') || null);

  const handleLogin = (id: string) => {
    setUserId(id);
    localStorage.setItem('userId', id);
  };

  const handleLogout = () => {
    setUserId(null);
    localStorage.removeItem('userId');
  };

  return (
    <Routes>
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login onLogin={handleLogin} />} />
      <Route
        path="/"
        element={<TransportSolver userId={userId} onLogout={handleLogout} />}
      />
      <Route
        path="/tables"
        element={
          userId ? (
            <PreviousTables userId={userId} />
          ) : (
            <Navigate to="/login" />
          )
        }
      />
    </Routes>
  );
}

export default App;