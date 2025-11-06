import { useState } from 'react';
import { BookOpen, Plus, Search, PlayCircle, FileText } from 'lucide-react';
import './RecipesManagement.css';

export function RecipesManagement({ recipes, onCreateRecipe, onLoadRecipe, onRefresh, loading }) {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({
    nome: '',
    descrizione: ''
  });
  const [errors, setErrors] = useState({});
  const [loadingRecipe, setLoadingRecipe] = useState(null);

  const filteredRecipes = recipes.filter(recipe =>
    recipe.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (recipe.descrizione && recipe.descrizione.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const validateForm = () => {
    const newErrors = {};
    if (!formData.nome.trim()) {
      newErrors.nome = 'Il nome della ricetta è obbligatorio';
    }
    if (formData.nome.trim().length > 200) {
      newErrors.nome = 'Il nome non può superare 200 caratteri';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      await onCreateRecipe(formData);
      setShowModal(false);
      setFormData({ nome: '', descrizione: '' });
      setErrors({});
      onRefresh();
    } catch (error) {
      setErrors({ submit: 'Errore durante la creazione della ricetta' });
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
    <div className="recipes-management">
      <div className="management-header">
        <div className="header-title-section">
          <BookOpen size={28} className="header-icon" />
          <h2 className="management-title">Gestione Ricette</h2>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
        >
          <Plus size={18} />
          Nuova Ricetta
        </button>
      </div>

      <div className="search-section">
        <div className="search-input-wrapper">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Cerca ricetta..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Caricamento ricette...</p>
        </div>
      ) : (
        <div className="recipes-grid">
          {filteredRecipes.length === 0 ? (
            <div className="empty-state">
              <BookOpen size={48} className="empty-icon" />
              <p className="empty-title">Nessuna ricetta trovata</p>
              <p className="empty-description">
                {searchTerm ? 'Prova a modificare i criteri di ricerca' : 'Inizia aggiungendo la prima ricetta'}
              </p>
            </div>
          ) : (
            filteredRecipes.map(recipe => (
              <div key={recipe.id} className="recipe-card">
                <div className="recipe-card-header">
                  <FileText size={24} className="recipe-icon" />
                  <span className="recipe-id">#{recipe.id}</span>
                </div>
                
                <h3 className="recipe-name">{recipe.nome}</h3>
                
                {recipe.descrizione && (
                  <p className="recipe-description">{recipe.descrizione}</p>
                )}
              
              </div>
            ))
          )}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Nuova Ricetta</h3>
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
                  Nome Ricetta *
                </label>
                <input
                  type="text"
                  id="nome"
                  name="nome"
                  className={`form-input ${errors.nome ? 'input-error' : ''}`}
                  value={formData.nome}
                  onChange={handleInputChange}
                  placeholder="Es. RICETTA_STANDARD"
                  maxLength="200"
                />
                {errors.nome && <span className="error-message">{errors.nome}</span>}
                <span className="input-hint">Il nome deve corrispondere a quello presente sulla macchina</span>
              </div>

              <div className="form-group">
                <label htmlFor="descrizione" className="form-label">
                  Descrizione
                </label>
                <textarea
                  id="descrizione"
                  name="descrizione"
                  className="form-textarea"
                  value={formData.descrizione}
                  onChange={handleInputChange}
                  placeholder="Descrizione della configurazione (opzionale)..."
                  rows="4"
                />
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
                  Crea Ricetta
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}