import { useState, useEffect } from 'react';
import { Users, BookOpen } from 'lucide-react';
import { RecipesClientsApiService } from '../../recipesApi';
import { ClientsManagement } from '../components/ClientsManagement/ClientsManagement';
import { RecipesManagement } from '../components/RecipesManagement/RecipesManagement';
import './ManagementPage.css';

export function ManagementPage() {
  const [activeTab, setActiveTab] = useState('clients');
  const [clients, setClients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [clientsData, recipesData] = await Promise.all([
        RecipesClientsApiService.getClients(),
        RecipesClientsApiService.getRecipes()
      ]);
      
      setClients(clientsData);
      setRecipes(recipesData);
    } catch (err) {
      setError(err.message);
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClient = async (clientData) => {
    try {
      await RecipesClientsApiService.createClient(clientData);
      await loadData();
    } catch (error) {
      throw new Error('Impossibile creare il cliente');
    }
  };

  const handleCreateRecipe = async (recipeData) => {
    try {
      await RecipesClientsApiService.createRecipe(recipeData);
      await loadData();
    } catch (error) {
      throw new Error('Impossibile creare la ricetta');
    }
  };

  const handleLoadRecipe = async (recipeName) => {
    try {
      return await RecipesClientsApiService.loadRecipeToMachine(recipeName);
    } catch (error) {
      throw new Error('Impossibile caricare la ricetta sulla macchina');
    }
  };

  return (
    <div className="management-page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">Gestione Sistema</h1>
          <p className="page-subtitle">
            Amministra clienti e ricette per la gestione della produzione
          </p>
        </div>

        <div className="tabs-container">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'clients' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('clients')}
            >
              <Users size={20} />
              Clienti
              <span className="tab-badge">{clients.length}</span>
            </button>
            <button
              className={`tab ${activeTab === 'recipes' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('recipes')}
            >
              <BookOpen size={20} />
              Ricette
              <span className="tab-badge">{recipes.length}</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="error-alert">
            <strong>Errore:</strong> {error}
            <button className="btn-retry" onClick={loadData}>
              Riprova
            </button>
          </div>
        )}

        <div className="tab-content">
          {activeTab === 'clients' ? (
            <ClientsManagement
              clients={clients}
              onCreateClient={handleCreateClient}
              onRefresh={loadData}
              loading={loading}
            />
          ) : (
            <RecipesManagement
              recipes={recipes}
              onCreateRecipe={handleCreateRecipe}
              onLoadRecipe={handleLoadRecipe}
              onRefresh={loadData}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  );
}