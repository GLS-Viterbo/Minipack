import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useMachineData } from './hooks/useMachineData';
import { Navbar } from './components/Navbar/Navbar';
import { DashboardPage } from './pages/DashboardPage';
import { ManagementPage } from './pages/ManagementPage';
import { LoadingSpinner, ErrorMessage } from './components/LoadingError/LoadingError';
import { CreaCommessa } from './components/CreaCommessa/CreaCommessa';
import { GestioneCommesse } from './components/GestioneCommesse/GestioneCommesse';
import './App.css';

function App() {
  const { data, loading, error, refresh, isPolling, togglePolling } = useMachineData(5000);

  return (
    <Router>
      <div className="app">
        <Navbar 
          isPolling={isPolling}
          onTogglePolling={togglePolling}
          onRefresh={refresh}
          lastUpdate={data?.timestamp}
        />
        
        <main className="main-content">
          <div className="container">
            <Routes>
              <Route 
                path="/" 
                element={
                  loading && !data ? (
                    <LoadingSpinner />
                  ) : error && !data ? (
                    <ErrorMessage error={error} onRetry={refresh} />
                  ) : (
                    <DashboardPage data={data} />
                  )
                } 
              />
              <Route 
                path="/management" 
                element={<ManagementPage />} 
              />
              <Route 
                path="/commesse" 
                element={
                  <div className="commesse-page">
                    <h1>Gestione Commesse</h1>
                    <CreaCommessa onCommessaCreata={() => window.location.reload()} />
                    <GestioneCommesse />
                  </div>
                } 
              />
              <Route 
                path="/commesse/nuova" 
                element={
                  <div className="commesse-page">
                    <h1>Nuova Commessa</h1>
                    <CreaCommessa onCommessaCreata={() => window.history.back()} />
                  </div>
                } 
              />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;