-- ============================================================================
-- SCHEMA DATABASE SQLite - MINIPACKTORRE MONITORING SYSTEM
-- Sistema di monitoraggio e tracciabilità produzione Industria 4.0
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABELLE ANAGRAFICHE
-- ============================================================================

-- Tabella clienti
CREATE TABLE IF NOT EXISTS clienti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(200) NOT NULL,
    partita_iva VARCHAR(20),
    codice_fiscale VARCHAR(16),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TABELLE RICETTE E PRODUZIONE
-- ============================================================================

-- Tabella ricette
CREATE TABLE IF NOT EXISTS ricette (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(200) NOT NULL UNIQUE,
    descrizione TEXT
);

-- ============================================================================
-- TABELLE GESTIONE COMMESSE
-- ============================================================================

-- Tabella commesse
CREATE TABLE IF NOT EXISTS commesse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    ricetta_id INTEGER NOT NULL,
    
    -- Quantità
    quantita_richiesta INTEGER NOT NULL,
    quantita_prodotta INTEGER DEFAULT 0,
    
    -- Date
    data_ordine DATE NOT NULL,
    data_consegna_prevista DATE,
    data_inizio_produzione TIMESTAMP,
    data_fine_produzione TIMESTAMP,
    
    -- Metadati
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (cliente_id) REFERENCES clienti(id) ON DELETE RESTRICT,
    FOREIGN KEY (ricetta_id) REFERENCES ricette(id) ON DELETE RESTRICT
);

-- ============================================================================
-- TABELLE MONITORAGGIO MACCHINA
-- ============================================================================

-- Tabella eventi macchina (log dettagliato)
CREATE TABLE IF NOT EXISTS eventi_macchina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    lavorazione_id INTEGER, -- NULL se fuori produzione
    
    -- Tipo evento
    tipo_evento VARCHAR(50) NOT NULL, -- AVVIO, ARRESTO, CAMBIO_STATO, CAMBIO_RICETTA, ALLARME, RESET, etc.
    
    -- Stato macchina
    stato_macchina VARCHAR(50), -- STOP_MANUALE, START_MANUALE, STOP_AUTOMATICO, START_AUTOMATICO, EMERGENZA
    
    -- Dati processo (JSON completo per flessibilità)
    dati_json TEXT,
    
    FOREIGN KEY (lavorazione_id) REFERENCES commesse(id) ON DELETE SET NULL
);

-- ============================================================================
-- TABELLE ALLARMI
-- ============================================================================

-- Tabella storico allarmi
CREATE TABLE IF NOT EXISTS allarmi_storico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_inizio TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    timestamp_fine TIMESTAMP,
    durata_secondi INTEGER,
    
    lavorazione_id INTEGER, -- NULL se fuori produzione
    
    -- Codice
    codice_allarme INTEGER NOT NULL,
    
    FOREIGN KEY (lavorazione_id) REFERENCES commesse(id) ON DELETE SET NULL
);

-- ============================================================================
-- INDICI PER PERFORMANCE
-- ============================================================================

-- Indici per ricerche frequenti
CREATE INDEX IF NOT EXISTS idx_eventi_timestamp ON eventi_macchina(timestamp);
CREATE INDEX IF NOT EXISTS idx_eventi_tipo ON eventi_macchina(tipo_evento);
CREATE INDEX IF NOT EXISTS idx_eventi_lavorazione ON eventi_macchina(lavorazione_id);

CREATE INDEX IF NOT EXISTS idx_allarmi_timestamp ON allarmi_storico(timestamp_inizio);
CREATE INDEX IF NOT EXISTS idx_allarmi_codice ON allarmi_storico(codice_allarme);
CREATE INDEX IF NOT EXISTS idx_allarmi_lavorazione ON allarmi_storico(lavorazione_id);
CREATE INDEX IF NOT EXISTS idx_allarmi_attivi ON allarmi_storico(timestamp_fine) WHERE timestamp_fine IS NULL;

CREATE INDEX IF NOT EXISTS idx_commesse_attive ON commesse(data_fine_produzione) WHERE data_fine_produzione IS NULL;
CREATE INDEX IF NOT EXISTS idx_commesse_cliente ON commesse(cliente_id);
CREATE INDEX IF NOT EXISTS idx_commesse_ricetta ON commesse(ricetta_id);