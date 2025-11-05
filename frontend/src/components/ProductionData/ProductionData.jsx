import { 
  Package, 
  FileText, 
  BarChart3, 
  Target 
} from 'lucide-react';
import './ProductionData.css';

export function ProductionData({ 
  recipe, 
  totalPieces, 
  partialPieces, 
  batchCounter 
}) {
  return (
    <div className="card production-card">
      <div className="card-header">
        <Package size={24} className="card-icon" />
        <h2 className="card-title">Dati Produzione</h2>
      </div>
      
      <div className="production-grid">
        <div className="production-item">
          <FileText size={20} className="production-icon" />
          <div className="production-content">
            <span className="production-label">Ricetta</span>
            <span className="production-value">{recipe || 'Nessuna ricetta'}</span>
          </div>
        </div>
        
        <div className="production-item">
          <BarChart3 size={20} className="production-icon" />
          <div className="production-content">
            <span className="production-label">Pezzi Totali</span>
            <span className="production-value production-number">
              {totalPieces.toLocaleString('it-IT')}
            </span>
          </div>
        </div>
        
        <div className="production-item">
          <BarChart3 size={20} className="production-icon" />
          <div className="production-content">
            <span className="production-label">Pezzi Parziali</span>
            <span className="production-value production-number">
              {partialPieces.toLocaleString('it-IT')}
            </span>
          </div>
        </div>
        
        <div className="production-item">
          <Target size={20} className="production-icon" />
          <div className="production-content">
            <span className="production-label">Contatore Lotto</span>
            <span className="production-value production-number">
              {batchCounter.toLocaleString('it-IT')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
