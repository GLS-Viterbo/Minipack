import { Loader, AlertTriangle, RefreshCw } from 'lucide-react';
import './LoadingError.css';

export function LoadingSpinner() {
  return (
    <div className="loading-container">
      <Loader className="loading-spinner" size={48} />
      <p className="loading-text">Caricamento dati in corso...</p>
    </div>
  );
}

export function ErrorMessage({ error, onRetry }) {
  return (
    <div className="error-container">
      <div className="error-card">
        <AlertTriangle className="error-icon" size={48} />
        <h2 className="error-title">Errore di Connessione</h2>
        <p className="error-message">{error}</p>
        <button className="error-button" onClick={onRetry}>
          <RefreshCw size={18} />
          <span>Riprova</span>
        </button>
      </div>
    </div>
  );
}
