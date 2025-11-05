const API_BASE_URL = '/api';

export class ApiService {
  /**
   * Recupera tutti i dati della macchina
   */
  static async getMachineData() {
    try {
      const response = await fetch(`${API_BASE_URL}/data`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching machine data:', error);
      throw error;
    }
  }

  /**
   * Verifica lo stato dell'API
   */
  static async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      console.error('Error checking API health:', error);
      throw error;
    }
  }

  /**
   * Placeholder per future funzionalità di caricamento ricette
   */
  static async loadRecipe(recipeName) {
    // TODO: Implementare quando il backend supporterà questa funzionalità
    console.log('loadRecipe not yet implemented:', recipeName);
    throw new Error('Recipe loading not yet implemented');
  }
}
