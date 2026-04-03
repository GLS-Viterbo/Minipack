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
  BarChart3,
  List,
  Layers
} from 'lucide-react';
import { StatsApiService } from '../services/statsApi';
import { SessioniApiService } from '../services/sessioniApi';
import { KPICard } from '../components/KPICard/KPICard';
import './StatsPage.css';

function formatDuration(seconds) {
  if (!seconds) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function StatsPage() {
  const [tab, setTab] = useState('kpi');

  const [dataInizio, setDataInizio] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });

  const [dataFine, setDataFine] = useState(new Date().toISOString().split('T')[0]);

  // KPI state
  const [kpi, setKpi] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sessioni state
  const [sessioni, setSessioni] = useState(null);
  const [sessioniLoading, setSessioniLoading] = useState(false);
  const [sessioniError, setSessioniError] = useState(null);

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

  const loadSessioni = async () => {
    setSessioniLoading(true);
    setSessioniError(null);
    try {
      const data = await SessioniApiService.getSessioni({ data_inizio: dataInizio, data_fine: dataFine, limit: 100 });
      setSessioni(data);
    } catch (err) {
      setSessioniError(err.message);
    } finally {
      setSessioniLoading(false);
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

        {/* Tab switcher */}
        <div className="stats-tabs">
          <button
            className={`stats-tab ${tab === 'kpi' ? 'active' : ''}`}
            onClick={() => setTab('kpi')}
          >
            <BarChart3 size={16} />
            KPI
          </button>
          <button
            className={`stats-tab ${tab === 'sessioni' ? 'active' : ''}`}
            onClick={() => setTab('sessioni')}
          >
            <List size={16} />
            Sessioni
          </button>
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
              {tab === 'kpi' ? (
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
              ) : (
                <button
                  className="btn btn-primary"
                  onClick={loadSessioni}
                  disabled={sessioniLoading}
                >
                  {sessioniLoading ? (
                    <>
                      <RefreshCw size={18} className="rotating" />
                      Caricamento...
                    </>
                  ) : (
                    <>
                      <List size={18} />
                      Carica Sessioni
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Bottoni Export (solo tab KPI) */}
          {tab === 'kpi' && kpi && (
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

        {/* Vista Sessioni */}
        {tab === 'sessioni' && (
          <>
            {sessioniError && (
              <div className="error-alert">
                <AlertTriangle size={20} />
                <div><strong>Errore:</strong> {sessioniError}</div>
                <button className="btn-retry" onClick={loadSessioni}>Riprova</button>
              </div>
            )}

            {sessioni && (
              <div className="sessioni-table-wrapper">
                {sessioni.length === 0 ? (
                  <div className="empty-state">
                    <List size={48} className="empty-icon" />
                    <h3>Nessuna sessione nel periodo</h3>
                    <p>Non sono state rilevate sessioni di produzione nel periodo selezionato.</p>
                  </div>
                ) : (
                  <table className="sessioni-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Ricetta</th>
                        <th>Inizio</th>
                        <th>Durata</th>
                        <th>Pezzi</th>
                        <th>Target</th>
                        <th>Origine</th>
                        <th>Stato</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessioni.map((s) => (
                        <tr key={s.id}>
                          <td className="col-id">{s.id}</td>
                          <td className="col-ricetta">{s.ricetta_nome}</td>
                          <td className="col-data">
                            {new Date(s.timestamp_inizio).toLocaleString('it-IT', {
                              day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                            })}
                          </td>
                          <td>{formatDuration(s.durata_secondi)}</td>
                          <td className="col-pezzi">{s.quantita_prodotta.toLocaleString()}</td>
                          <td>{s.contatore_lotto > 0 ? s.contatore_lotto.toLocaleString() : '—'}</td>
                          <td>
                            <span className={`origine-badge ${s.origine}`}>
                              {s.origine === 'pannello' ? 'Pannello' : `Commessa #${s.commessa_id}`}
                            </span>
                          </td>
                          <td>
                            <span className={`stato-badge ${s.stato}`}>
                              {s.stato === 'attiva' ? '● Attiva' : 'Chiusa'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {!sessioni && !sessioniLoading && !sessioniError && (
              <div className="empty-state">
                <List size={64} className="empty-icon" />
                <h3>Seleziona un periodo</h3>
                <p>Scegli le date e clicca "Carica Sessioni" per vedere le sessioni rilevate automaticamente.</p>
              </div>
            )}
          </>
        )}

        {/* KPI Dashboard */}
        {tab === 'kpi' && kpi && (
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

            {/* Sessioni Pannello */}
            {kpi.sessioni_pannello?.totale > 0 && (
              <div className="stats-section">
                <h2 className="section-title">
                  <Activity size={20} />
                  Sessioni Pannello
                  <span className="section-subtitle">produzione senza commessa attiva</span>
                </h2>
                <div className="kpi-grid-4">
                  <KPICard
                    title="Sessioni"
                    value={kpi.sessioni_pannello.totale}
                    icon={List}
                    color="blue"
                  />
                  <KPICard
                    title="Pezzi Pannello"
                    value={kpi.sessioni_pannello.pezzi_prodotti.toLocaleString()}
                    icon={Package}
                    color="purple"
                  />
                  <KPICard
                    title="Ore Pannello"
                    value={kpi.sessioni_pannello.ore_produzione}
                    unit="h"
                    icon={Clock}
                    color="orange"
                  />
                  <KPICard
                    title="Pezzi/Ora Pannello"
                    value={kpi.sessioni_pannello.pezzi_ora_medio}
                    icon={Activity}
                    color="green"
                  />
                </div>
              </div>
            )}

            {/* Totale Produzione */}
            {kpi.totale?.pezzi_prodotti > 0 && (
              <div className="stats-section stats-section-totale">
                <h2 className="section-title">
                  <Layers size={20} />
                  Totale Produzione
                  <span className="section-subtitle">commesse + pannello, senza doppio conteggio</span>
                </h2>
                <div className="kpi-grid-2">
                  <KPICard
                    title="Pezzi Totali"
                    value={kpi.totale.pezzi_prodotti.toLocaleString()}
                    icon={Package}
                    color="blue"
                  />
                  <KPICard
                    title="Ore Totali"
                    value={kpi.totale.ore_produzione}
                    unit="h"
                    icon={Clock}
                    color="green"
                  />
                </div>
              </div>
            )}

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

        {/* Stato Iniziale KPI */}
        {tab === 'kpi' && !kpi && !loading && !error && (
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