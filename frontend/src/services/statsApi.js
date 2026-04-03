const API_BASE_URL = '/api';

export class StatsApiService {
  /**
   * Recupera i KPI per il periodo specificato
   */
  static async getKPI(dataInizio, dataFine) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/report/kpi?data_inizio=${dataInizio}&data_fine=${dataFine}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching KPI:', error);
      throw error;
    }
  }

  /**
   * Recupera i dati completi di produzione per il periodo specificato
   */
  static async getDatiCompleti(dataInizio, dataFine) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/report/dati-completi?data_inizio=${dataInizio}&data_fine=${dataFine}`
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching production data:', error);
      throw error;
    }
  }

  /**
   * Scarica export CSV
   */
  static downloadCSV(dataInizio, dataFine) {
    const url = `${API_BASE_URL}/export/produzione?data_inizio=${dataInizio}&data_fine=${dataFine}&formato=csv`;
    window.open(url, '_blank');
  }

  /**
   * Scarica export Excel
   */
  static downloadExcel(dataInizio, dataFine) {
    const url = `${API_BASE_URL}/export/produzione?data_inizio=${dataInizio}&data_fine=${dataFine}&formato=excel`;
    window.open(url, '_blank');
  }

  /**
   * Scarica export JSON
   */
  static downloadJSON(dataInizio, dataFine) {
    const url = `${API_BASE_URL}/export/produzione?data_inizio=${dataInizio}&data_fine=${dataFine}&formato=json`;
    window.open(url, '_blank');
  }
}