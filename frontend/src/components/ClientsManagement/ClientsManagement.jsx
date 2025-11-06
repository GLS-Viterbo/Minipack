import { useState } from 'react';
import { Users, Plus, Search, Building2 } from 'lucide-react';
import './ClientsManagement.css';

export function ClientsManagement({ clients, onCreateClient, onRefresh, loading }) {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    nome: '',
    partita_iva: '',
    codice_fiscale: ''
  });
  const [errors, setErrors] = useState({});

  const filteredClients = clients.filter(client =>
    client.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (client.partita_iva && client.partita_iva.includes(searchTerm))
  );

  const validateForm = () => {
    const newErrors = {};
    if (!formData.nome.trim()) {
      newErrors.nome = 'Il nome è obbligatorio';
    }
    if (formData.partita_iva && !/^\d{11}$/.test(formData.partita_iva.replace(/\s/g, ''))) {
      newErrors.partita_iva = 'La Partita IVA deve contenere 11 cifre';
    }
    if (formData.codice_fiscale && formData.codice_fiscale.length !== 16) {
      newErrors.codice_fiscale = 'Il Codice Fiscale deve contenere 16 caratteri';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      await onCreateClient(formData);
      setShowModal(false);
      setFormData({ nome: '', partita_iva: '', codice_fiscale: '' });
      setErrors({});
      onRefresh();
    } catch (error) {
      setErrors({ submit: 'Errore durante la creazione del cliente' });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  return (
    <div className="clients-management">
      <div className="management-header">
        <div className="header-title-section">
          <Users size={28} className="header-icon" />
          <h2 className="management-title">Gestione Clienti</h2>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
        >
          <Plus size={18} />
          Nuovo Cliente
        </button>
      </div>

      <div className="search-section">
        <div className="search-input-wrapper">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Cerca per nome o P.IVA..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Caricamento clienti...</p>
        </div>
      ) : (
        <div className="clients-grid">
          {filteredClients.length === 0 ? (
            <div className="empty-state">
              <Users size={48} className="empty-icon" />
              <p className="empty-title">Nessun cliente trovato</p>
              <p className="empty-description">
                {searchTerm ? 'Prova a modificare i criteri di ricerca' : 'Inizia aggiungendo il primo cliente'}
              </p>
            </div>
          ) : (
            filteredClients.map(client => (
              <div key={client.id} className="client-card">
                <div className="client-card-header">
                  <Building2 size={24} className="client-icon" />
                  <span className="client-id">#{client.id}</span>
                </div>
                <h3 className="client-name">{client.nome}</h3>
                <div className="client-details">
                  {client.partita_iva && (
                    <div className="client-detail-item">
                      <span className="detail-label">P.IVA:</span>
                      <span className="detail-value">{client.partita_iva}</span>
                    </div>
                  )}
                  {client.codice_fiscale && (
                    <div className="client-detail-item">
                      <span className="detail-label">C.F.:</span>
                      <span className="detail-value">{client.codice_fiscale}</span>
                    </div>
                  )}
                  <div className="client-detail-item">
                    <span className="detail-label">Creato:</span>
                    <span className="detail-value">
                      {new Date(client.created_at).toLocaleDateString('it-IT')}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Nuovo Cliente</h3>
              <button 
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="modal-form">
              <div className="form-group">
                <label htmlFor="nome" className="form-label">
                  Nome / Ragione Sociale *
                </label>
                <input
                  type="text"
                  id="nome"
                  name="nome"
                  className={`form-input ${errors.nome ? 'input-error' : ''}`}
                  value={formData.nome}
                  onChange={handleInputChange}
                  placeholder="Es. ACME Corporation S.r.l."
                />
                {errors.nome && <span className="error-message">{errors.nome}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="partita_iva" className="form-label">
                  Partita IVA
                </label>
                <input
                  type="text"
                  id="partita_iva"
                  name="partita_iva"
                  className={`form-input ${errors.partita_iva ? 'input-error' : ''}`}
                  value={formData.partita_iva}
                  onChange={handleInputChange}
                  placeholder="12345678901"
                  maxLength="11"
                />
                {errors.partita_iva && <span className="error-message">{errors.partita_iva}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="codice_fiscale" className="form-label">
                  Codice Fiscale
                </label>
                <input
                  type="text"
                  id="codice_fiscale"
                  name="codice_fiscale"
                  className={`form-input ${errors.codice_fiscale ? 'input-error' : ''}`}
                  value={formData.codice_fiscale}
                  onChange={handleInputChange}
                  placeholder="RSSMRA80A01H501U"
                  maxLength="16"
                  style={{ textTransform: 'uppercase' }}
                />
                {errors.codice_fiscale && <span className="error-message">{errors.codice_fiscale}</span>}
              </div>

              {errors.submit && (
                <div className="error-banner">{errors.submit}</div>
              )}

              <div className="modal-actions">
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Annulla
                </button>
                <button type="submit" className="btn btn-primary">
                  Crea Cliente
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}