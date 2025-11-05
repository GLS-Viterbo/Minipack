import { useMachineData } from './hooks/useMachineData';
import { Header } from './components/Header/Header';
import { StatusCard } from './components/StatusCard/StatusCard';
import { SystemInfo } from './components/SystemInfo/SystemInfo';
import { ProductionData } from './components/ProductionData/ProductionData';
import { TemperatureData } from './components/TemperatureData/TemperatureData';
import { PositionData } from './components/PositionData/PositionData';
import { LoadingSpinner, ErrorMessage } from './components/LoadingError/LoadingError';
import './App.css';

function App() {
  const { data, loading, error, refresh, isPolling, togglePolling } = useMachineData(5000);

  if (loading && !data) {
    return <LoadingSpinner />;
  }

  if (error && !data) {
    return <ErrorMessage error={error} onRetry={refresh} />;
  }

  return (
    <div className="app">
      <Header 
        isPolling={isPolling}
        onTogglePolling={togglePolling}
        onRefresh={refresh}
        lastUpdate={data?.timestamp}
      />
      
      <main className="main-content">
        <div className="container">
          <div className="dashboard-grid">
            <StatusCard 
              status={data.status}
              alarms={data.alarms}
              hasAlarms={data.has_alarms}
            />
            
            <div className="sidebar-section">
              <SystemInfo 
                softwareName={data.software_name}
                softwareVersion={data.software_version}
              />
              
              <PositionData 
                trianglePosition={data.triangle_position}
                centerSealingPosition={data.center_sealing_position}
              />
            </div>
            
            <div className="main-section">
              <ProductionData 
                recipe={data.recipe}
                totalPieces={data.total_pieces}
                partialPieces={data.partial_pieces}
                batchCounter={data.batch_counter}
              />
              
              <TemperatureData 
                lateralBarTemp={data.lateral_bar_temp}
                frontalBarTemp={data.frontal_bar_temp}
              />
            </div>
          </div>
          
          {/* Sezione placeholder per future funzionalità */}
          <div className="future-features">
            <div className="card future-card">
              <h3 className="future-title">Funzionalità Future</h3>
              <p className="future-description">
                Questa sezione verrà utilizzata per il caricamento delle ricette e altre funzionalità avanzate.
              </p>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="footer">
        <div className="container">
          <p className="footer-text">
            © 2024 Elco Elettronica Automation Srl - MinipackTorre Dashboard v1.0.0
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
