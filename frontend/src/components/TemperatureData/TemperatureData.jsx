import { Thermometer } from 'lucide-react';
import './TemperatureData.css';

export function TemperatureData({ lateralBarTemp, frontalBarTemp }) {
  const getTemperatureClass = (temp) => {
    if (temp < 50) return 'temp-cold';
    if (temp < 100) return 'temp-warm';
    if (temp < 150) return 'temp-hot';
    return 'temp-very-hot';
  };

  return (
    <div className="card temperature-card">
      <div className="card-header">
        <Thermometer size={24} className="card-icon" />
        <h2 className="card-title">Temperature</h2>
      </div>
      
      <div className="temperature-grid">
        <div className="temperature-item">
          <div className="temperature-header">
            <Thermometer size={18} className="temperature-icon" />
            <span className="temperature-label">Barra Laterale</span>
          </div>
          <div className="temperature-display">
            <span className={`temperature-value ${getTemperatureClass(lateralBarTemp)}`}>
              {lateralBarTemp.toFixed(1)}
            </span>
            <span className="temperature-unit">°C</span>
          </div>
          <div className="temperature-bar">
            <div 
              className={`temperature-fill ${getTemperatureClass(lateralBarTemp)}`}
              style={{ width: `${Math.min((lateralBarTemp / 200) * 100, 100)}%` }}
            />
          </div>
        </div>
        
        <div className="temperature-item">
          <div className="temperature-header">
            <Thermometer size={18} className="temperature-icon" />
            <span className="temperature-label">Barra Frontale</span>
          </div>
          <div className="temperature-display">
            <span className={`temperature-value ${getTemperatureClass(frontalBarTemp)}`}>
              {frontalBarTemp.toFixed(1)}
            </span>
            <span className="temperature-unit">°C</span>
          </div>
          <div className="temperature-bar">
            <div 
              className={`temperature-fill ${getTemperatureClass(frontalBarTemp)}`}
              style={{ width: `${Math.min((frontalBarTemp / 200) * 100, 100)}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
