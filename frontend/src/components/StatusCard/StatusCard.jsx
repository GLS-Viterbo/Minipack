import { 
  Circle, 
  AlertTriangle, 
  Play, 
  Square, 
  AlertCircle 
} from 'lucide-react';
import './StatusCard.css';

export function StatusCard({ status, alarms, hasAlarms }) {
  const getStatusIcon = () => {
    if (status.emergenza) {
      return <AlertCircle className="status-icon status-icon-emergency" size={32} />;
    } else if (status.start_automatico) {
      return <Play className="status-icon status-icon-running" size={32} />;
    } else if (status.stop_automatico) {
      return <Square className="status-icon status-icon-ready" size={32} />;
    } else {
      return <Circle className="status-icon status-icon-stopped" size={32} />;
    }
  };

  const getStatusClass = () => {
    if (status.emergenza) return 'status-emergency';
    if (status.start_automatico) return 'status-running';
    if (status.stop_automatico) return 'status-ready';
    return 'status-stopped';
  };

  return (
    <div className="card status-card">
      <div className="card-header">
        <h2 className="card-title">Stato Macchina</h2>
      </div>
      
      <div className="status-main">
        <div className={`status-indicator ${getStatusClass()}`}>
          {getStatusIcon()}
          <div className="status-text">
            <span className="status-label">Stato Corrente</span>
            <span className="status-value">{status.status_text}</span>
          </div>
        </div>
      </div>

      {hasAlarms && (
        <div className="alarms-section">
          <div className="alarms-header">
            <AlertTriangle size={20} />
            <h3>Allarmi Attivi ({alarms.length})</h3>
          </div>
          <div className="alarms-list">
            {alarms.map((alarm, index) => (
              <div key={index} className="alarm-item">
                <span className="alarm-code">A{String(alarm.code).padStart(3, '0')}</span>
                <span className="alarm-message">{alarm.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!hasAlarms && (
        <div className="no-alarms">
          <Circle className="no-alarms-icon" size={20} />
          <span>Nessun allarme attivo</span>
        </div>
      )}
    </div>
  );
}
