import { useState, useEffect, useCallback } from 'react';
import { ApiService } from '../services/api';

/**
 * Hook personalizzato per gestire il polling dei dati della macchina
 * @param {number} refreshInterval - Intervallo di aggiornamento in millisecondi (default: 5000)
 */
export function useMachineData(refreshInterval = 5000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const machineData = await ApiService.getMachineData();
      setData(machineData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Fetch iniziale
    fetchData();

    // Setup polling se abilitato
    if (isPolling && refreshInterval > 0) {
      const intervalId = setInterval(fetchData, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [fetchData, isPolling, refreshInterval]);

  const refresh = useCallback(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  const togglePolling = useCallback(() => {
    setIsPolling(prev => !prev);
  }, []);

  return {
    data,
    loading,
    error,
    refresh,
    isPolling,
    togglePolling
  };
}
