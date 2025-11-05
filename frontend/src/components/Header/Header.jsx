import { Activity, RefreshCw, Pause, Play } from 'lucide-react';
import './Header.css';

export function Header({ isPolling, onTogglePolling, onRefresh, lastUpdate }) {
  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <div className="header-left">
            <Activity className="header-icon" size={32} />
            <div>
              <h1 className="header-title">MinipackTorre Dashboard</h1>
              <p className="header-subtitle">Monitoraggio Real-Time Industria 4.0</p>
            </div>
          </div>
          
          <div className="header-right">
            {lastUpdate && (
              <div className="last-update">
                <span className="last-update-label">Ultimo aggiornamento:</span>
                <span className="last-update-time">
                  {new Date(lastUpdate).toLocaleTimeString('it-IT')}
                </span>
              </div>
            )}
            
            <div className="header-actions">
              <button 
                className="btn btn-secondary"
                onClick={onTogglePolling}
                title={isPolling ? 'Pausa aggiornamento automatico' : 'Riprendi aggiornamento automatico'}
              >
                {isPolling ? <Pause size={18} /> : <Play size={18} />}
                <span>{isPolling ? 'Pausa' : 'Riprendi'}</span>
              </button>
              
              <button 
                className="btn btn-primary"
                onClick={onRefresh}
                title="Aggiorna dati"
              >
                <RefreshCw size={18} />
                <span>Aggiorna</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
