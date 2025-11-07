const API_BASE_URL = '/api';

export class RecipesClientsApiService {
  /**
   * CLIENTI
   */
  static async getClients() {
    try {
      const response = await fetch(`${API_BASE_URL}/clienti`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching clients:', error);
      throw error;
    }
  }

  static async createClient(clientData) {
    try {
      const response = await fetch(`${API_BASE_URL}/clienti`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(clientData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating client:', error);
      throw error;
    }
  }

  static async getClient(clientId) {
    try {
      const response = await fetch(`${API_BASE_URL}/clienti/${clientId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching client:', error);
      throw error;
    }
  }

  /**
   * RICETTE
   */
  static async getRecipes() {
    try {
      const response = await fetch(`${API_BASE_URL}/ricette`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching recipes:', error);
      throw error;
    }
  }

  static async createRecipe(recipeData) {
    try {
      const response = await fetch(`${API_BASE_URL}/ricette`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(recipeData),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error creating recipe:', error);
      throw error;
    }
  }

  static async loadRecipeToMachine(recipeName) {
    try {
      const response = await fetch(`${API_BASE_URL}/load-recipe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ recipe_name: recipeName }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error loading recipe to machine:', error);
      throw error;
    }
  }
  /**
 * Elimina un cliente
 */
static async deleteClient(clientId) {
  try {
    const response = await fetch(`${API_BASE_URL}/clienti/${clientId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error deleting client:', error);
    throw error;
  }
}

/**
 * Elimina una ricetta
 */
static async deleteRecipe(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/ricette/${recipeId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error deleting recipe:', error);
    throw error;
  }
}
}