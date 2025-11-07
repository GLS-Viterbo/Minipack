import React, { useState, useEffect } from 'react';
import { 
  Package, 
  Play, 
  XCircle, 
  CheckCircle2, 
  Clock,
  AlertTriangle,
  RefreshCw,
  Loader,
  TrendingUp
} from 'lucide-react';
import './GestioneCommesse.css';

export function GestioneCommesse() {
  const [commesse, setCommesse] = useState([]);
  const [loading, setLoading] = useState(true);
  const [operationLoading, setOperationLoading] = useState(null);
  const [error, setError] = useState(null);
  const [filtroStato, setFiltroStato] = useState('tutte');

  useEffect(() => {
    loadCommesse();
    // Ricarica ogni 10 secondi
    const interval = setInterval(loadCommesse, 10000);
    return () => clearInterval(interval);
  }, [filtroStato]);

  const loadCommesse = async () => {
    try {
      let url = '/api/commesse';
      
      if (filtroStato !== 'tutte') {
        url += `?stato=${filtroStato}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Errore caricamento commesse');
      
      const data = await response.json();
      setCommesse(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const caricaRicetta = async (commessaId) => {
    setOperationLoading(commessaId);
    setError(null);

    try {
      const response = await fetch(`/api/commesse/${commessaId}/carica-ricetta`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Errore caricamento ricetta');
      }

      await loadCommesse();
      alert('Ricetta caricata con successo!');
    } catch (err) {
      setError(err.message);
      alert(`Errore: ${err.message}`);
    } finally {
      setOperationLoading(null);
    }
  };

  const annullaCommessa = async (commessaId) => {
    if (!confirm('Sei sicuro di voler annullare questa commessa?')) {
      return;
    }

    setOperationLoading(commessaId);
    setError(null);

    try {
      const response = await fetch(`/api/commesse/${commessaId}/annulla`, {
        method: 'POST'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Errore annullamento commessa');
      }

      await loadCommesse();
      alert('Commessa annullata');
    } catch (err) {
      setError(err.message);
      alert(`Errore: ${err.message}`);
    } finally {
      setOperationLoading(null);
    }
  };

  const getStatoStyle = (stato) => {
    const styles = {
      'in_attesa': { bg: '#fef3c7', color: '#92400e', icon: Clock },
      'ricetta_caricata': { bg: '#dbeafe', color: '#1e40af', icon: CheckCircle2 },
      'in_lavorazione': { bg: '#d1fae5', color: '#065f46', icon: TrendingUp },
      'completata': { bg: '#d1fae5', color: '#047857', icon: CheckCircle2 },
      'annullata': { bg: '#fee2e2', color: '#991b1b', icon: XCircle },
      'errore': { bg: '#fee2e2', color: '#991b1b', icon: AlertTriangle }
    };
    return styles[stato] || { bg: '#f3f4f6', color: '#6b7280', icon: Package };
  };

  const getPrioritaStyle = (priorita) => {
    const styles = {
      'bassa': { bg: '#f3f4f6', color: '#6b7280' },
      'normale': { bg: '#dbeafe', color: '#1e40af' },
      'alta': { bg: '#fef3c7', color: '#92400e' },
      'urgente': { bg: '#fee2e2', color: '#991b1b' }
    };
    return styles[priorita] || styles.normale;
  };

  const getStatoLabel = (stato) => {
    const labels = {
      'in_attesa': 'In Attesa',
      'ricetta_caricata': 'Ricetta Caricata',
      'in_lavorazione': 'In Lavorazione',
      'completata': 'Completata',
      'annullata': 'Annullata',
      'errore': 'Errore'
    };
    return labels[stato] || stato;
  };

  const calcolaProgresso = (prodotta, richiesta) => {
    if (richiesta === 0) return 0;
    return Math.min(100, Math.round((prodotta / richiesta) * 100));
  };

  if (loading) {
    return (
      <div className="gestione-commesse-loading">
        <Loader className="spin" size={40} />
        <p>Caricamento commesse...</p>
      </div>
    );
  }

  return (
    <div className="gestione-commesse">
      <div className="gestione-header">
        <div className="header-title">
          <Package size={28} />
          <h2>Gestione Commesse</h2>
        </div>
        
        <button onClick={loadCommesse} className="btn btn-refresh">
          <RefreshCw size={18} />
          Aggiorna
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Filtri */}
      <div className="filtri-container">
        <label>Filtra per stato:</label>
        <div className="filtri-buttons">
          {['tutte', 'in_attesa', 'ricetta_caricata', 'in_lavorazione', 'completata'].map(stato => (
            <button
              key={stato}
              className={`filtro-btn ${filtroStato === stato ? 'active' : ''}`}
              onClick={() => setFiltroStato(stato)}
            >
              {stato === 'tutte' ? 'Tutte' : getStatoLabel(stato)}
            </button>
          ))}
        </div>
      </div>

      {/* Lista commesse */}
      {commesse.length === 0 ? (
        <div className="empty-state">
          <Package size={64} />
          <h3>Nessuna commessa trovata</h3>
          <p>Crea una nuova commessa per iniziare</p>
        </div>
      ) : (
        <div className="commesse-grid">
          {commesse.map(commessa => {
            const statoStyle = getStatoStyle(commessa.stato);
            const prioritaStyle = getPrioritaStyle(commessa.priorita);
            const progresso = calcolaProgresso(commessa.quantita_prodotta, commessa.quantita_richiesta);
            const StatusIcon = statoStyle.icon;

            return (
              <div key={commessa.id} className="commessa-card">
                <div className="commessa-header">
                  <div className="commessa-id">
                    <Package size={20} />
                    <span>Commessa #{commessa.id}</span>
                  </div>
                  <div className="badges">
                    <span 
                      className="badge badge-priorita"
                      style={{ 
                        backgroundColor: prioritaStyle.bg,
                        color: prioritaStyle.color 
                      }}
                    >
                      {commessa.priorita.toUpperCase()}
                    </span>
                    <span 
                      className="badge badge-stato"
                      style={{ 
                        backgroundColor: statoStyle.bg,
                        color: statoStyle.color 
                      }}
                    >
                      <StatusIcon size={14} />
                      {getStatoLabel(commessa.stato)}
                    </span>
                  </div>
                </div>

                <div className="commessa-body">
                  <div className="info-row">
                    <span className="label">Cliente:</span>
                    <span className="value">ID {commessa.cliente_id}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Ricetta:</span>
                    <span className="value">ID {commessa.ricetta_id}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Quantità:</span>
                    <span className="value">
                      <strong>{commessa.quantita_prodotta}</strong> / {commessa.quantita_richiesta} pezzi
                    </span>
                  </div>
                  
                  {/* Barra progresso */}
                  {commessa.stato !== 'in_attesa' && (
                    <div className="progresso-container">
                      <div className="progresso-bar">
                        <div 
                          className="progresso-fill"
                          style={{ width: `${progresso}%` }}
                        >
                          <span className="progresso-text">{progresso}%</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {commessa.data_consegna_prevista && (
                    <div className="info-row">
                      <span className="label">Consegna prevista:</span>
                      <span className="value">{commessa.data_consegna_prevista}</span>
                    </div>
                  )}

                  {commessa.note && (
                    <div className="note-section">
                      <p className="note-text">{commessa.note}</p>
                    </div>
                  )}
                </div>

                {/* Azioni */}
                <div className="commessa-actions">
                  {commessa.stato === 'in_attesa' && (
                    <>
                      <button
                        className="btn btn-primary"
                        onClick={() => caricaRicetta(commessa.id)}
                        disabled={operationLoading === commessa.id}
                      >
                        {operationLoading === commessa.id ? (
                          <Loader className="spin" size={16} />
                        ) : (
                          <Play size={16} />
                        )}
                        Carica Ricetta
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => annullaCommessa(commessa.id)}
                        disabled={operationLoading === commessa.id}
                      >
                        <XCircle size={16} />
                        Annulla
                      </button>
                    </>
                  )}

                  {commessa.stato === 'ricetta_caricata' && (
                    <div className="status-message success">
                      <CheckCircle2 size={16} />
                      <span>Ricetta caricata - Pronta per l'avvio</span>
                    </div>
                  )}

                  {commessa.stato === 'in_lavorazione' && (
                    <div className="status-message info">
                      <TrendingUp size={16} />
                      <span>Lavorazione in corso...</span>
                    </div>
                  )}

                  {commessa.stato === 'completata' && (
                    <div className="status-message success">
                      <CheckCircle2 size={16} />
                      <span>Commessa completata!</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}