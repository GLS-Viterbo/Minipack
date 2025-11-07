import React, { useState, useEffect } from 'react';
import { Plus, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import './CreaCommessa.css';

export function CreaCommessa({ onCommessaCreata }) {
  const [clienti, setClienti] = useState([]);
  const [ricette, setRicette] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const [formData, setFormData] = useState({
    cliente_id: '',
    ricetta_id: '',
    quantita_richiesta: '',
    data_consegna_prevista: '',
    priorita: 'normale',
    note: ''
  });

  // Carica clienti e ricette all'avvio
  useEffect(() => {
    loadClienti();
    loadRicette();
  }, []);

  const loadClienti = async () => {
    try {
      const response = await fetch('/api/clienti');
      const data = await response.json();
      setClienti(data);
    } catch (err) {
      console.error('Errore caricamento clienti:', err);
    }
  };

  const loadRicette = async () => {
    try {
      const response = await fetch('/api/ricette');
      const data = await response.json();
      setRicette(data);
    } catch (err) {
      console.error('Errore caricamento ricette:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // Validazione base
      if (!formData.cliente_id || !formData.ricetta_id || !formData.quantita_richiesta) {
        throw new Error('Compila tutti i campi obbligatori');
      }

      if (parseInt(formData.quantita_richiesta) <= 0) {
        throw new Error('La quantità deve essere maggiore di zero');
      }

      // Invia richiesta
      const response = await fetch('/api/commesse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cliente_id: parseInt(formData.cliente_id),
          ricetta_id: parseInt(formData.ricetta_id),
          quantita_richiesta: parseInt(formData.quantita_richiesta),
          data_consegna_prevista: formData.data_consegna_prevista || null,
          priorita: formData.priorita,
          note: formData.note || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Errore durante la creazione');
      }

      const commessa = await response.json();
      
      setSuccess(true);
      
      // Reset form
      setFormData({
        cliente_id: '',
        ricetta_id: '',
        quantita_richiesta: '',
        data_consegna_prevista: '',
        priorita: 'normale',
        note: ''
      });

      // Notifica componente padre
      if (onCommessaCreata) {
        onCommessaCreata(commessa);
      }

      // Nascondi messaggio successo dopo 3 secondi
      setTimeout(() => setSuccess(false), 3000);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="crea-commessa-card">
      <div className="card-header">
        <Plus className="icon" />
        <h2>Nuova Commessa</h2>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <CheckCircle size={20} />
          <span>Commessa creata con successo!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="commessa-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="cliente_id">
              Cliente <span className="required">*</span>
            </label>
            <select
              id="cliente_id"
              name="cliente_id"
              value={formData.cliente_id}
              onChange={handleChange}
              required
              disabled={loading}
            >
              <option value="">Seleziona cliente...</option>
              {clienti.map(cliente => (
                <option key={cliente.id} value={cliente.id}>
                  {cliente.nome}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="ricetta_id">
              Ricetta <span className="required">*</span>
            </label>
            <select
              id="ricetta_id"
              name="ricetta_id"
              value={formData.ricetta_id}
              onChange={handleChange}
              required
              disabled={loading}
            >
              <option value="">Seleziona ricetta...</option>
              {ricette.map(ricetta => (
                <option key={ricetta.id} value={ricetta.id}>
                  {ricetta.nome}
                </option>
              ))}
            </select>
            {formData.ricetta_id && ricette.find(r => r.id === parseInt(formData.ricetta_id))?.descrizione && (
              <small className="form-hint">
                {ricette.find(r => r.id === parseInt(formData.ricetta_id)).descrizione}
              </small>
            )}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="quantita_richiesta">
              Quantità Richiesta <span className="required">*</span>
            </label>
            <input
              type="number"
              id="quantita_richiesta"
              name="quantita_richiesta"
              value={formData.quantita_richiesta}
              onChange={handleChange}
              min="1"
              required
              disabled={loading}
              placeholder="Es: 1000"
            />
          </div>

          <div className="form-group">
            <label htmlFor="data_consegna_prevista">
              Data Consegna Prevista
            </label>
            <input
              type="date"
              id="data_consegna_prevista"
              name="data_consegna_prevista"
              value={formData.data_consegna_prevista}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="priorita">Priorità</label>
            <select
              id="priorita"
              name="priorita"
              value={formData.priorita}
              onChange={handleChange}
              disabled={loading}
            >
              <option value="bassa">Bassa</option>
              <option value="normale">Normale</option>
              <option value="alta">Alta</option>
              <option value="urgente">Urgente</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="note">Note</label>
          <textarea
            id="note"
            name="note"
            value={formData.note}
            onChange={handleChange}
            disabled={loading}
            rows="3"
            placeholder="Note aggiuntive sulla commessa..."
          />
        </div>

        <button 
          type="submit" 
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader className="icon spin" />
              Creazione in corso...
            </>
          ) : (
            <>
              <Plus className="icon" />
              Crea Commessa
            </>
          )}
        </button>
      </form>
    </div>
  );
}