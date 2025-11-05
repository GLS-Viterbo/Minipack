import { Move, Navigation } from 'lucide-react';
import './PositionData.css';

export function PositionData({ trianglePosition, centerSealingPosition }) {
  return (
    <div className="card position-card">
      <div className="card-header">
        <Move size={24} className="card-icon" />
        <h2 className="card-title">Posizioni</h2>
      </div>
      
      <div className="position-grid">
        <div className="position-item">
          <Navigation size={20} className="position-icon" />
          <div className="position-content">
            <span className="position-label">Triangolo</span>
            <div className="position-value-wrapper">
              <span className="position-value">{trianglePosition.toFixed(2)}</span>
              <span className="position-unit">mm</span>
            </div>
          </div>
        </div>
        
        <div className="position-item">
          <Navigation size={20} className="position-icon" />
          <div className="position-content">
            <span className="position-label">Center Sealing</span>
            <div className="position-value-wrapper">
              <span className="position-value">{centerSealingPosition.toFixed(2)}</span>
              <span className="position-unit">mm</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
