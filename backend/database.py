"""
Repository per gestione database SQLite - MinipackTorre Monitoring System
Gestisce operazioni CRUD e monitoraggio periodico dello stato macchina
"""

import aiosqlite
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class Cliente:
    """Modello Cliente"""
    id: Optional[int]
    nome: str
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Ricetta:
    """Modello Ricetta"""
    id: Optional[int]
    nome: str
    descrizione: Optional[str] = None


@dataclass
class Commessa:
    """Modello Commessa"""
    id: Optional[int]
    cliente_id: int
    ricetta_id: int
    quantita_richiesta: int
    data_ordine: str
    quantita_prodotta: int = 0
    data_consegna_prevista: Optional[str] = None
    data_inizio_produzione: Optional[datetime] = None
    data_fine_produzione: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class EventoMacchina:
    """Modello Evento Macchina"""
    id: Optional[int]
    timestamp: datetime
    lavorazione_id: Optional[int]
    tipo_evento: str
    stato_macchina: Optional[str]
    dati_json: Optional[str]


@dataclass
class Allarme:
    """Modello Allarme"""
    id: Optional[int]
    timestamp_inizio: datetime
    timestamp_fine: Optional[datetime]
    durata_secondi: Optional[int]
    lavorazione_id: Optional[int]
    codice_allarme: int


class DatabaseRepository:
    """
    Repository principale per operazioni su database SQLite
    Gestisce monitoraggio periodico e inserimento eventi
    """

    def __init__(self, db_path: str = "minipack_monitoring.db"):
        """
        Inizializza il repository
        
        Args:
            db_path: Percorso del file database SQLite
        """
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        
        # Stato precedente per rilevare cambiamenti
        self._ultimo_stato: Optional[Dict[str, Any]] = None
        self._allarmi_attivi: Dict[int, int] = {}  # {codice_allarme: id_record}

    async def connect(self):
        """Connette al database"""
        self.db = await aiosqlite.connect(self.db_path)
        self.db.row_factory = aiosqlite.Row
        await self._init_schema()

    async def disconnect(self):
        """Disconnette dal database"""
        if self.db:
            await self.db.close()

    async def _init_schema(self):
        """Inizializza lo schema del database"""
        schema_path = Path(__file__).parent / "schema.sql"
        
        if schema_path.exists():
            async with aiosqlite.connect(self.db_path) as db:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                await db.executescript(schema)
                await db.commit()

    # ========================================================================
    # CLIENTI
    # ========================================================================

    async def get_cliente(self, cliente_id: int) -> Optional[Cliente]:
        """Recupera un cliente per ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM clienti WHERE id = ?", (cliente_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Cliente(**dict(row))
        return None

    async def get_clienti(self) -> List[Cliente]:
        """Recupera tutti i clienti"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM clienti ORDER BY nome") as cursor:
                rows = await cursor.fetchall()
                return [Cliente(**dict(row)) for row in rows]

    async def create_cliente(self, cliente: Cliente) -> int:
        """Crea un nuovo cliente"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO clienti (nome, partita_iva, codice_fiscale)
                   VALUES (?, ?, ?)""",
                (cliente.nome, cliente.partita_iva, cliente.codice_fiscale)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_cliente(self, cliente: Cliente):
        """Aggiorna un cliente esistente"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE clienti 
                   SET nome = ?, partita_iva = ?, codice_fiscale = ?, 
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (cliente.nome, cliente.partita_iva, cliente.codice_fiscale, cliente.id)
            )
            await db.commit()

    async def delete_cliente(self, cliente_id: int):
        """Elimina un cliente"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM clienti WHERE id = ?", (cliente_id,))
            await db.commit()

    # ========================================================================
    # RICETTE
    # ========================================================================

    async def get_ricetta(self, ricetta_id: int) -> Optional[Ricetta]:
        """Recupera una ricetta per ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM ricette WHERE id = ?", (ricetta_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Ricetta(**dict(row))
        return None

    async def get_ricetta_by_nome(self, nome: str) -> Optional[Ricetta]:
        """Recupera una ricetta per nome"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM ricette WHERE nome = ?", (nome,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Ricetta(**dict(row))
        return None

    async def get_ricette(self) -> List[Ricetta]:
        """Recupera tutte le ricette"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM ricette ORDER BY nome") as cursor:
                rows = await cursor.fetchall()
                return [Ricetta(**dict(row)) for row in rows]

    async def create_ricetta(self, ricetta: Ricetta) -> int:
        """Crea una nuova ricetta"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO ricette (nome, descrizione)
                   VALUES (?, ?)""",
                (ricetta.nome, ricetta.descrizione)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_ricetta(self, ricetta: Ricetta):
        """Aggiorna una ricetta esistente"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE ricette 
                   SET nome = ?, descrizione = ?
                   WHERE id = ?""",
                (ricetta.nome, ricetta.descrizione, ricetta.id)
            )
            await db.commit()

    async def delete_ricetta(self, ricetta_id: int):
        """Elimina una ricetta"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM ricette WHERE id = ?", (ricetta_id,))
            await db.commit()

    # ========================================================================
    # COMMESSE
    # ========================================================================

    async def get_commessa(self, commessa_id: int) -> Optional[Commessa]:
        """Recupera una commessa per ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM commesse WHERE id = ?", (commessa_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Commessa(**dict(row))
        return None

    async def get_commesse(self, attive_only: bool = False) -> List[Commessa]:
        """
        Recupera le commesse
        
        Args:
            attive_only: Se True, recupera solo commesse non completate
        """
        query = "SELECT * FROM commesse"
        if attive_only:
            query += " WHERE data_fine_produzione IS NULL"
        query += " ORDER BY data_ordine DESC"
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [Commessa(**dict(row)) for row in rows]

    async def create_commessa(self, commessa: Commessa) -> int:
        """Crea una nuova commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO commesse 
                   (cliente_id, ricetta_id, quantita_richiesta, quantita_prodotta,
                    data_ordine, data_consegna_prevista)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (commessa.cliente_id, commessa.ricetta_id, commessa.quantita_richiesta,
                 commessa.quantita_prodotta, commessa.data_ordine, 
                 commessa.data_consegna_prevista)
            )
            await db.commit()
            return cursor.lastrowid

    async def update_commessa(self, commessa: Commessa):
        """Aggiorna una commessa esistente"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE commesse 
                   SET cliente_id = ?, ricetta_id = ?, 
                       quantita_richiesta = ?, quantita_prodotta = ?,
                       data_ordine = ?, data_consegna_prevista = ?,
                       data_inizio_produzione = ?, data_fine_produzione = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (commessa.cliente_id, commessa.ricetta_id,
                 commessa.quantita_richiesta, commessa.quantita_prodotta,
                 commessa.data_ordine, commessa.data_consegna_prevista,
                 commessa.data_inizio_produzione, commessa.data_fine_produzione,
                 commessa.id)
            )
            await db.commit()

    async def incrementa_quantita_prodotta(self, commessa_id: int, incremento: int = 1):
        """Incrementa la quantità prodotta per una commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE commesse 
                   SET quantita_prodotta = quantita_prodotta + ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (incremento, commessa_id)
            )
            await db.commit()

    # ========================================================================
    # EVENTI MACCHINA
    # ========================================================================

    async def insert_evento_macchina(
        self,
        tipo_evento: str,
        stato_macchina: Optional[str] = None,
        lavorazione_id: Optional[int] = None,
        dati: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Inserisce un nuovo evento macchina
        
        Args:
            tipo_evento: Tipo evento (AVVIO, ARRESTO, CAMBIO_STATO, ecc.)
            stato_macchina: Stato corrente macchina
            lavorazione_id: ID lavorazione associata (opzionale)
            dati: Dati aggiuntivi da salvare come JSON
        """
        dati_json = json.dumps(dati) if dati else None
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO eventi_macchina 
                   (tipo_evento, stato_macchina, lavorazione_id, dati_json)
                   VALUES (?, ?, ?, ?)""",
                (tipo_evento, stato_macchina, lavorazione_id, dati_json)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_eventi_macchina(
        self,
        limit: int = 100,
        lavorazione_id: Optional[int] = None
    ) -> List[EventoMacchina]:
        """
        Recupera gli eventi macchina
        
        Args:
            limit: Numero massimo di eventi da recuperare
            lavorazione_id: Filtra per lavorazione specifica (opzionale)
        """
        query = "SELECT * FROM eventi_macchina"
        params = []
        
        if lavorazione_id:
            query += " WHERE lavorazione_id = ?"
            params.append(lavorazione_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [EventoMacchina(**dict(row)) for row in rows]

    # ========================================================================
    # ALLARMI
    # ========================================================================

    async def insert_allarme(
        self,
        codice_allarme: int,
        lavorazione_id: Optional[int] = None
    ) -> int:
        """Inserisce un nuovo allarme attivo"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO allarmi_storico 
                   (codice_allarme, lavorazione_id)
                   VALUES (?, ?)""",
                (codice_allarme, lavorazione_id)
            )
            await db.commit()
            record_id = cursor.lastrowid
            
            # Traccia l'allarme attivo
            self._allarmi_attivi[codice_allarme] = record_id
            
            return record_id

    async def chiudi_allarme(self, codice_allarme: int):
        """Chiude un allarme quando viene risolto"""
        if codice_allarme not in self._allarmi_attivi:
            return
        
        record_id = self._allarmi_attivi[codice_allarme]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE allarmi_storico 
                   SET timestamp_fine = CURRENT_TIMESTAMP,
                       durata_secondi = (
                           CAST((julianday(CURRENT_TIMESTAMP) - julianday(timestamp_inizio)) * 86400 AS INTEGER)
                       )
                   WHERE id = ?""",
                (record_id,)
            )
            await db.commit()
        
        # Rimuovi dalla lista allarmi attivi
        del self._allarmi_attivi[codice_allarme]

    async def get_allarmi_storico(
        self,
        limit: int = 100,
        lavorazione_id: Optional[int] = None
    ) -> List[Allarme]:
        """
        Recupera lo storico allarmi
        
        Args:
            limit: Numero massimo di allarmi da recuperare
            lavorazione_id: Filtra per lavorazione specifica (opzionale)
        """
        query = "SELECT * FROM allarmi_storico"
        params = []
        
        if lavorazione_id:
            query += " WHERE lavorazione_id = ?"
            params.append(lavorazione_id)
        
        query += " ORDER BY timestamp_inizio DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Allarme(**dict(row)) for row in rows]

    async def get_statistiche_allarmi(self, giorni: int = 30) -> List[Dict[str, Any]]:
        """
        Recupera statistiche allarmi per gli ultimi N giorni
        
        Args:
            giorni: Numero di giorni da considerare
            
        Returns:
            Lista di dizionari con codice_allarme, conteggio, durata_media
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT 
                       codice_allarme,
                       COUNT(*) as conteggio,
                       AVG(durata_secondi) as durata_media_secondi,
                       SUM(durata_secondi) as durata_totale_secondi
                   FROM allarmi_storico
                   WHERE timestamp_inizio >= datetime('now', '-' || ? || ' days')
                   GROUP BY codice_allarme
                   ORDER BY conteggio DESC""",
                (giorni,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ========================================================================
    # MONITORAGGIO PERIODICO
    # ========================================================================

    async def monitor_machine_state(self, machine_data: Dict[str, Any], lavorazione_id: Optional[int] = None):
        """
        Monitora lo stato della macchina e registra eventi/allarmi quando necessario
        
        Args:
            machine_data: Dati correnti della macchina (da MinipackTorreOPCUA)
            lavorazione_id: ID lavorazione corrente (se in produzione)
        """
        # Estrai dati rilevanti
        status_flags = machine_data.get('status', {})
        allarmi_correnti = set(alarm['code'] for alarm in machine_data.get('alarms', []))
        
        stato_attuale = self._determina_stato_macchina(status_flags)
        
        # ====================================================================
        # 1. RILEVAMENTO CAMBIO STATO
        # ====================================================================
        if self._ultimo_stato is None or self._ultimo_stato.get('stato') != stato_attuale:
            await self.insert_evento_macchina(
                tipo_evento="CAMBIO_STATO",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'status_flags': status_flags,
                    'timestamp': machine_data.get('timestamp')
                }
            )
        
        # ====================================================================
        # 2. RILEVAMENTO CAMBIO RICETTA
        # ====================================================================
        ricetta_corrente = machine_data.get('recipe')
        if self._ultimo_stato and self._ultimo_stato.get('ricetta') != ricetta_corrente:
            await self.insert_evento_macchina(
                tipo_evento="CAMBIO_RICETTA",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'ricetta_precedente': self._ultimo_stato.get('ricetta'),
                    'ricetta_nuova': ricetta_corrente,
                    'timestamp': machine_data.get('timestamp')
                }
            )
        
        # ====================================================================
        # 3. GESTIONE ALLARMI
        # ====================================================================
        # Allarmi precedenti
        allarmi_precedenti = set(self._allarmi_attivi.keys())
        
        # Nuovi allarmi (presenti ora ma non prima)
        nuovi_allarmi = allarmi_correnti - allarmi_precedenti
        for codice in nuovi_allarmi:
            await self.insert_allarme(codice, lavorazione_id)
            await self.insert_evento_macchina(
                tipo_evento="ALLARME",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'codice_allarme': codice,
                    'timestamp': machine_data.get('timestamp')
                }
            )
        
        # Allarmi risolti (presenti prima ma non ora)
        allarmi_risolti = allarmi_precedenti - allarmi_correnti
        for codice in allarmi_risolti:
            await self.chiudi_allarme(codice)
            await self.insert_evento_macchina(
                tipo_evento="ALLARME_RISOLTO",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'codice_allarme': codice,
                    'timestamp': machine_data.get('timestamp')
                }
            )
        
        # ====================================================================
        # 4. AGGIORNA STATO PRECEDENTE
        # ====================================================================
        self._ultimo_stato = {
            'stato': stato_attuale,
            'ricetta': ricetta_corrente,
            'timestamp': machine_data.get('timestamp')
        }

    def _determina_stato_macchina(self, status_flags: Dict[str, bool]) -> str:
        """Determina lo stato macchina dai flag"""
        if status_flags.get('emergenza'):
            return "EMERGENZA"
        elif status_flags.get('start_automatico'):
            return "START_AUTOMATICO"
        elif status_flags.get('start_manuale'):
            return "START_MANUALE"
        elif status_flags.get('stop_automatico'):
            return "STOP_AUTOMATICO"
        elif status_flags.get('stop_manuale'):
            return "STOP_MANUALE"
        else:
            return "SCONOSCIUTO"

    # ========================================================================
    # UTILITY
    # ========================================================================

    async def get_database_stats(self) -> Dict[str, Any]:
        """Recupera statistiche generali del database"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Conteggi tabelle
            async with db.execute("SELECT COUNT(*) FROM clienti") as cursor:
                stats['num_clienti'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM ricette") as cursor:
                stats['num_ricette'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM commesse") as cursor:
                stats['num_commesse_totali'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM commesse WHERE data_fine_produzione IS NULL"
            ) as cursor:
                stats['num_commesse_attive'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM eventi_macchina") as cursor:
                stats['num_eventi'] = (await cursor.fetchone())[0]
            
            async with db.execute("SELECT COUNT(*) FROM allarmi_storico") as cursor:
                stats['num_allarmi_totali'] = (await cursor.fetchone())[0]
            
            async with db.execute(
                "SELECT COUNT(*) FROM allarmi_storico WHERE timestamp_fine IS NULL"
            ) as cursor:
                stats['num_allarmi_attivi'] = (await cursor.fetchone())[0]
            
            return stats