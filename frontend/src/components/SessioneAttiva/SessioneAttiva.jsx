import { useState, useEffect, useRef } from 'react';
import { Activity, Package, Clock, Target } from 'lucide-react';
import { SessioniApiService } from '../../services/sessioniApi';
import './SessioneAttiva.css';

function formatDuration(isoTimestamp) {
  const seconds = Math.floor((Date.now() - new Date(isoTimestamp).getTime()) / 1000);
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function SessioneAttiva() {
  const [sessione, setSessione] = useState(null);
  const [durata, setDurata] = useState('');
  const intervalRef = useRef(null);

  useEffect(() => {
    const fetchSessione = async () => {
      try {
        const data = await SessioniApiService.getSessioneAttiva();
        setSessione(data);
      } catch {
        setSessione(null);
      }
    };

    fetchSessione();
    const pollId = setInterval(fetchSessione, 5000);
    return () => clearInterval(pollId);
  }, []);

  useEffect(() => {
    if (!sessione) {
      clearInterval(intervalRef.current);
      return;
    }
    const update = () => setDurata(formatDuration(sessione.timestamp_inizio));
    update();
    intervalRef.current = setInterval(update, 1000);
    return () => clearInterval(intervalRef.current);
  }, [sessione?.timestamp_inizio]);

  if (!sessione) return null;

  const hasTarget = sessione.contatore_lotto > 0;
  const progressPct = hasTarget
    ? Math.min(100, Math.round((sessione.quantita_prodotta / sessione.contatore_lotto) * 100))
    : null;
  const isPannello = sessione.origine === 'pannello';

  return (
    <div className="sessione-attiva">
      <div className="sessione-header">
        <div className="sessione-title">
          <Activity size={18} className="sessione-icon-pulse" />
          <span>Sessione in corso</span>
        </div>
        <span className={`sessione-badge ${isPannello ? 'badge-pannello' : 'badge-commessa'}`}>
          {isPannello ? 'Pannello' : `Commessa #${sessione.commessa_id}`}
        </span>
      </div>

      <div className="sessione-body">
        <div className="sessione-info">
          <div className="sessione-stat">
            <Package size={16} />
            <span className="stat-label">Ricetta</span>
            <span className="stat-value">{sessione.ricetta_nome}</span>
          </div>
          <div className="sessione-stat">
            <Activity size={16} />
            <span className="stat-label">Pezzi</span>
            <span className="stat-value stat-big">{sessione.quantita_prodotta.toLocaleString()}</span>
            {hasTarget && (
              <span className="stat-target">/ {sessione.contatore_lotto.toLocaleString()}</span>
            )}
          </div>
          <div className="sessione-stat">
            <Clock size={16} />
            <span className="stat-label">Durata</span>
            <span className="stat-value">{durata}</span>
          </div>
          {hasTarget && (
            <div className="sessione-stat">
              <Target size={16} />
              <span className="stat-label">Avanzamento</span>
              <span className="stat-value">{progressPct}%</span>
            </div>
          )}
        </div>

        {hasTarget && (
          <div className="sessione-progress">
            <div
              className="sessione-progress-bar"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
