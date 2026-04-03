const API_BASE_URL = '/api';

export class SessioniApiService {
  static async getSessioneAttiva() {
    const response = await fetch(`${API_BASE_URL}/sessioni/attiva`);
    if (response.status === 404) return null;
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }

  static async getSessioni({ limit = 50, data_inizio, data_fine } = {}) {
    const params = new URLSearchParams({ limit });
    if (data_inizio) params.append('data_inizio', data_inizio);
    if (data_fine) params.append('data_fine', data_fine);
    const response = await fetch(`${API_BASE_URL}/sessioni?${params}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  }
}
