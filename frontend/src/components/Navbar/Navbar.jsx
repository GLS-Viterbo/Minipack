import { Link, useLocation } from 'react-router-dom';
import { Home, Settings, RefreshCw } from 'lucide-react';
import './Navbar.css';

export function Navbar({ isPolling, onTogglePolling, onRefresh, lastUpdate }) {
  const location = useLocation();
  
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="header-left">
            <div className="logo">
              <div className="logo-icon">MP</div>
              <div className="logo-text">
                <h1 className="logo-title">MinipackTorre</h1>
                <span className="logo-subtitle">Dashboard v1.0</span>
              </div>
            </div>
          </div>
          
          <nav className="navbar">
            <Link 
              to="/" 
              className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
            >
              <Home size={20} />
              <span>Dashboard</span>
            </Link>
            <Link 
              to="/management" 
              className={`nav-link ${location.pathname === '/management' ? 'active' : ''}`}
            >
              <Settings size={20} />
              <span>Gestione</span>
            </Link>
          </nav>
          
          {location.pathname === '/' && (
            <div className="header-right">
              <button
                className={`btn btn-icon ${isPolling ? 'btn-active' : ''}`}
                onClick={onTogglePolling}
                title={isPolling ? 'Pausa aggiornamenti' : 'Avvia aggiornamenti'}
              >
                <RefreshCw size={20} className={isPolling ? 'rotating' : ''} />
              </button>
              
              <button
                className="btn btn-secondary"
                onClick={onRefresh}
                title="Aggiorna ora"
              >
                Aggiorna
              </button>
              
              {lastUpdate && (
                <span className="last-update">
                  Ultimo aggiornamento: {new Date(lastUpdate).toLocaleTimeString('it-IT')}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}