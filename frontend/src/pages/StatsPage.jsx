import { useState } from 'react';
import {
  TrendingUp,
  Package,
  Activity,
  AlertTriangle,
  FileSpreadsheet,
  FileJson,
  Calendar,
  RefreshCw,
  Clock,
  CheckCircle,
  BarChart3
} from 'lucide-react';
import { StatsApiService } from '../services/statsApi';
import { KPICard } from '../components/KPICard/KPICard';
import './StatsPage.css';

export function StatsPage() {
  const [dataInizio, setDataInizio] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });

  const [dataFine, setDataFine] = useState(new Date().toISOString().split('T')[0]);

  const [kpi, setKpi] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadKPI = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await StatsApiService.getKPI(dataInizio, dataFine);
      setKpi(data);
    } catch (err) {
      setError(err.message);
      console.error('Error loading KPI:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stats-page">
      <div className="container">
        <div className="page-header">
          <h1 className="page-title">Statistiche Produzione e KPI</h1>
          <p className="page-subtitle">
            Analizza le performance di produzione e scarica i report
          </p>
        </div>

        {/* Form Selezione Periodo */}
        <div className="stats-controls">
          <div className="date-range-selector">
            <div className="form-group">
              <label htmlFor="data-inizio">
                <Calendar size={16} />
                Data Inizio
              </label>
              <input
                type="date"
                id="data-inizio"
                value={dataInizio}
                onChange={(e) => setDataInizio(e.target.value)}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="data-fine">
                <Calendar size={16} />
                Data Fine
              </label>
              <input
                type="date"
                id="data-fine"
                value={dataFine}
                onChange={(e) => setDataFine(e.target.value)}
                className="form-input"
              />
            </div>
            <div className="form-group">
              <button
                className="btn btn-primary"
                onClick={loadKPI}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <RefreshCw size={18} className="rotating" />
                    Caricamento...
                  </>
                ) : (
                  <>
                    <BarChart3 size={18} />
                    Calcola KPI
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Bottoni Export */}
          {kpi && (
            <div className="export-buttons">
              <button
                className="btn btn-success"
                onClick={() => StatsApiService.downloadExcel(dataInizio, dataFine)}
                title="Scarica Excel con grafici e KPI"
              >
                <FileSpreadsheet size={18} />
                Excel
              </button>
              <button
                className="btn btn-outline"
                onClick={() => StatsApiService.downloadJSON(dataInizio, dataFine)}
                title="Scarica JSON completo"
              >
                <FileJson size={18} />
                JSON
              </button>
            </div>
          )}
        </div>

        {/* Errore */}
        {error && (
          <div className="error-alert">
            <AlertTriangle size={20} />
            <div>
              <strong>Errore:</strong> {error}
            </div>
            <button className="btn-retry" onClick={loadKPI}>
              Riprova
            </button>
          </div>
        )}

        {/* KPI Dashboard */}
        {kpi && (
          <div className="kpi-dashboard">
            {/* Periodo */}
            <div className="stats-section">
              <h2 className="section-title">
                <Calendar size={20} />
                Periodo Analizzato
              </h2>
              <div className="kpi-grid-3">
                <KPICard
                  title="Giorni Calendario"
                  value={kpi.periodo.giorni_calendario}
                  icon={Calendar}
                  color="blue"
                />
                <KPICard
                  title="Giorni Lavorati"
                  value={kpi.periodo.giorni_lavorati}
                  icon={CheckCircle}
                  color="green"
                />
                <KPICard
                  title="Giorni Inattivi"
                  value={kpi.periodo.giorni_inattivi}
                  icon={Clock}
                  color="orange"
                />
              </div>
            </div>

            {/* Produzione */}
            <div className="stats-section">
              <h2 className="section-title">
                <Package size={20} />
                Produzione
              </h2>
              <div className="kpi-grid-4">
                <KPICard
                  title="Pezzi Prodotti"
                  value={kpi.produzione.pezzi_prodotti.toLocaleString()}
                  icon={Package}
                  color="blue"
                />
                <KPICard
                  title="Pezzi Richiesti"
                  value={kpi.produzione.pezzi_richiesti.toLocaleString()}
                  icon={TrendingUp}
                  color="purple"
                />
                <KPICard
                  title="Completamento"
                  value={kpi.produzione.tasso_completamento_pezzi_perc}
                  unit="%"
                  icon={CheckCircle}
                  color="green"
                />
                <KPICard
                  title="Pezzi/Ora Medio"
                  value={kpi.produzione.pezzi_ora_medio}
                  icon={Activity}
                  color="orange"
                />
              </div>
            </div>

            {/* Commesse */}
            <div className="stats-section">
              <h2 className="section-title">
                <Package size={20} />
                Commesse
              </h2>
              <div className="kpi-grid-4">
                <KPICard
                  title="Totali"
                  value={kpi.commesse.totali}
                  icon={Package}
                  color="blue"
                />
                <KPICard
                  title="Completate"
                  value={kpi.commesse.completate}
                  icon={CheckCircle}
                  color="green"
                />
                <KPICard
                  title="In Corso"
                  value={kpi.commesse.in_corso}
                  icon={Activity}
                  color="orange"
                />
                <KPICard
                  title="In Attesa"
                  value={kpi.commesse.in_attesa}
                  icon={Clock}
                  color="purple"
                />
              </div>
              <div className="kpi-grid-2">
                <KPICard
                  title="Tasso Completamento"
                  value={kpi.commesse.tasso_completamento_perc}
                  unit="%"
                  icon={TrendingUp}
                  color="green"
                />
                <KPICard
                  title="Tempo Medio Commessa"
                  value={kpi.commesse.tempo_medio_commessa_ore}
                  unit="ore"
                  icon={Clock}
                  color="blue"
                />
              </div>
            </div>

            {/* Tempi Produzione */}
            <div className="stats-section">
              <h2 className="section-title">
                <Clock size={20} />
                Tempi Produzione
              </h2>
              <div className="kpi-grid-4">
                <KPICard
                  title="Ore Produzione Commesse"
                  value={kpi.tempi.ore_produzione_commesse}
                  unit="h"
                  icon={Activity}
                  color="blue"
                />
                <KPICard
                  title="Fermo Durante Commesse"
                  value={kpi.tempi.ore_fermo_durante_commesse}
                  unit="h"
                  icon={AlertTriangle}
                  color="orange"
                />
                <KPICard
                  title="Fermo Fuori Commesse"
                  value={kpi.tempi.ore_fermo_fuori_commesse}
                  unit="h"
                  icon={AlertTriangle}
                  color="purple"
                />
                <KPICard
                  title="Ore Nette Produzione"
                  value={kpi.tempi.ore_nette}
                  unit="h"
                  icon={CheckCircle}
                  color="green"
                />
              </div>
            </div>

            {/* Allarmi */}
            <div className="stats-section">
              <h2 className="section-title">
                <AlertTriangle size={20} />
                Allarmi
              </h2>
              <div className="kpi-grid-3">
                <KPICard
                  title="Totale Occorrenze"
                  value={kpi.allarmi.totale_occorrenze}
                  icon={AlertTriangle}
                  color="red"
                />
                <KPICard
                  title="Tempo Fermo Totale"
                  value={kpi.allarmi.tempo_fermo_totale_ore}
                  unit="ore"
                  icon={Clock}
                  color="orange"
                />
                <KPICard
                  title="Allarmi per Giorno Lavorato"
                  value={kpi.allarmi.allarmi_per_giorno_lavorato}
                  icon={Activity}
                  color="red"
                />
              </div>
            </div>
          </div>
        )}

        {/* Stato Iniziale */}
        {!kpi && !loading && !error && (
          <div className="empty-state">
            <BarChart3 size={64} className="empty-icon" />
            <h3>Seleziona un periodo</h3>
            <p>
              Scegli le date di inizio e fine, poi clicca su "Calcola KPI" per visualizzare le statistiche di produzione.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}