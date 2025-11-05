import { Info, Code } from 'lucide-react';
import './SystemInfo.css';

export function SystemInfo({ softwareName, softwareVersion }) {
  return (
    <div className="card system-info-card">
      <div className="card-header">
        <Info size={24} className="card-icon" />
        <h2 className="card-title">Informazioni Sistema</h2>
      </div>
      
      <div className="info-grid">
        <div className="info-item">
          <Code size={18} className="info-icon" />
          <div className="info-content">
            <span className="info-label">Software</span>
            <span className="info-value">{softwareName}</span>
          </div>
        </div>
        
        <div className="info-item">
          <div className="info-content">
            <span className="info-label">Versione</span>
            <span className="info-value">{softwareVersion}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
