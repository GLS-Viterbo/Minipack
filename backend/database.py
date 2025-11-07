"""
Repository per gestione database SQLite - MinipackTorre Monitoring System
Gestisce operazioni CRUD e monitoraggio periodico dello stato macchina
"""

import aiosqlite
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Cliente:
    """Modello Cliente"""
    id: Optional[int]
    nome: str
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


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
    data_inizio_produzione: Optional[str] = None
    data_fine_produzione: Optional[str] = None
    stato: str = 'in_attesa'
    priorita: str = 'normale'
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class EventoCommessa:
    """Modello Evento Commessa"""
    id: Optional[int]
    commessa_id: int
    timestamp: str
    tipo_evento: str
    dettagli: Optional[str] = None
    utente: Optional[str] = None


@dataclass
class EventoMacchina:
    """Modello Evento Macchina"""
    id: Optional[int]
    timestamp: str
    lavorazione_id: Optional[int]
    tipo_evento: str
    stato_macchina: Optional[str]
    dati_json: Optional[str]


@dataclass
class Allarme:
    """Modello Allarme"""
    id: Optional[int]
    timestamp_inizio: str
    timestamp_fine: Optional[str]
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

    async def get_commesse(self, filtro_stato: Optional[str] = None) -> List[Commessa]:
        """
        Recupera tutte le commesse, opzionalmente filtrate per stato
        
        Args:
            filtro_stato: Se specificato, filtra per questo stato
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            if filtro_stato:
                query = "SELECT * FROM commesse WHERE stato = ? ORDER BY priorita DESC, data_ordine DESC"
                params = (filtro_stato,)
            else:
                query = "SELECT * FROM commesse ORDER BY data_ordine DESC"
                params = ()
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [Commessa(**dict(row)) for row in rows]

    async def get_commessa_attiva(self) -> Optional[Commessa]:
        """Recupera la commessa attualmente in lavorazione (se esiste)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM commesse 
                   WHERE stato IN ('in_lavorazione', 'ricetta_caricata') 
                   ORDER BY data_inizio_produzione DESC 
                   LIMIT 1"""
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Commessa(**dict(row))
        return None

    async def create_commessa(self, commessa: Commessa) -> int:
        """Crea una nuova commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO commesse (
                    cliente_id, ricetta_id, quantita_richiesta, quantita_prodotta,
                    data_ordine, data_consegna_prevista, stato, priorita, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    commessa.cliente_id, commessa.ricetta_id, commessa.quantita_richiesta,
                    commessa.quantita_prodotta, commessa.data_ordine, 
                    commessa.data_consegna_prevista, commessa.stato, commessa.priorita,
                    commessa.note
                )
            )
            await db.commit()
            commessa_id = cursor.lastrowid
            
            # Log evento creazione
            await self.insert_evento_commessa(
                commessa_id=commessa_id,
                tipo_evento='creata',
                dettagli=json.dumps({
                    'quantita': commessa.quantita_richiesta,
                    'priorita': commessa.priorita
                })
            )
            
            return commessa_id

    async def update_commessa(self, commessa: Commessa):
        """Aggiorna una commessa esistente"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE commesse 
                   SET cliente_id = ?, ricetta_id = ?, quantita_richiesta = ?,
                       quantita_prodotta = ?, data_ordine = ?, data_consegna_prevista = ?,
                       data_inizio_produzione = ?, data_fine_produzione = ?,
                       stato = ?, priorita = ?, note = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (
                    commessa.cliente_id, commessa.ricetta_id, commessa.quantita_richiesta,
                    commessa.quantita_prodotta, commessa.data_ordine, 
                    commessa.data_consegna_prevista, commessa.data_inizio_produzione,
                    commessa.data_fine_produzione, commessa.stato, commessa.priorita,
                    commessa.note, commessa.id
                )
            )
            await db.commit()

    async def update_stato_commessa(self, commessa_id: int, nuovo_stato: str, dettagli: Optional[Dict] = None):
        """
        Aggiorna lo stato di una commessa e registra l'evento
        
        Args:
            commessa_id: ID della commessa
            nuovo_stato: Nuovo stato ('in_attesa', 'ricetta_caricata', 'in_lavorazione', 'completata', 'annullata', 'errore')
            dettagli: Dettagli aggiuntivi da loggare
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Aggiorna timestamp specifici in base allo stato
            extra_updates = ""
            if nuovo_stato == 'in_lavorazione':
                extra_updates = ", data_inizio_produzione = CURRENT_TIMESTAMP"
            elif nuovo_stato in ('completata', 'annullata'):
                extra_updates = ", data_fine_produzione = CURRENT_TIMESTAMP"
            
            await db.execute(
                f"""UPDATE commesse 
                   SET stato = ?, updated_at = CURRENT_TIMESTAMP {extra_updates}
                   WHERE id = ?""",
                (nuovo_stato, commessa_id)
            )
            await db.commit()
            
            # Log evento
            evento_tipo = {
                'ricetta_caricata': 'ricetta_caricata',
                'in_lavorazione': 'avviata',
                'completata': 'completata',
                'annullata': 'annullata',
                'errore': 'errore'
            }.get(nuovo_stato, 'cambio_stato')
            
            await self.insert_evento_commessa(
                commessa_id=commessa_id,
                tipo_evento=evento_tipo,
                dettagli=json.dumps(dettagli) if dettagli else None
            )

    async def update_quantita_prodotta(self, commessa_id: int, quantita: int):
        """Aggiorna la quantità prodotta di una commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE commesse 
                   SET quantita_prodotta = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (quantita, commessa_id)
            )
            await db.commit()

    async def delete_commessa(self, commessa_id: int):
        """Elimina una commessa (CASCADE elimina anche gli eventi)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM commesse WHERE id = ?", (commessa_id,))
            await db.commit()

    # ========================================================================
    # EVENTI COMMESSA
    # ========================================================================

    async def insert_evento_commessa(
        self, 
        commessa_id: int, 
        tipo_evento: str,
        dettagli: Optional[str] = None,
        utente: Optional[str] = None
    ) -> int:
        """Inserisce un evento per una commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO eventi_commessa (commessa_id, tipo_evento, dettagli, utente)
                   VALUES (?, ?, ?, ?)""",
                (commessa_id, tipo_evento, dettagli, utente)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_eventi_commessa(self, commessa_id: int, limit: int = 50) -> List[EventoCommessa]:
        """Recupera gli eventi di una specifica commessa"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM eventi_commessa 
                   WHERE commessa_id = ?
                   ORDER BY timestamp DESC 
                   LIMIT ?""",
                (commessa_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [EventoCommessa(**dict(row)) for row in rows]

    # ========================================================================
    # EVENTI MACCHINA
    # ========================================================================

    async def insert_evento_macchina(
        self,
        tipo_evento: str,
        stato_macchina: Optional[str] = None,
        lavorazione_id: Optional[int] = None,
        dati: Optional[Dict] = None
    ) -> int:
        """Inserisce un evento macchina"""
        dati_json = json.dumps(dati) if dati else None
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO eventi_macchina (tipo_evento, stato_macchina, lavorazione_id, dati_json)
                   VALUES (?, ?, ?, ?)""",
                (tipo_evento, stato_macchina, lavorazione_id, dati_json)
            )
            await db.commit()
            return cursor.lastrowid

    async def get_eventi_macchina(self, limit: int = 100) -> List[EventoMacchina]:
        """Recupera gli ultimi eventi macchina"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM eventi_macchina ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [EventoMacchina(**dict(row)) for row in rows]

    # ========================================================================
    # ALLARMI
    # ========================================================================

    async def start_allarme(self, codice_allarme: int, lavorazione_id: Optional[int] = None) -> int:
        """Registra l'inizio di un allarme"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO allarmi_storico (codice_allarme, lavorazione_id)
                   VALUES (?, ?)""",
                (codice_allarme, lavorazione_id)
            )
            await db.commit()
            allarme_id = cursor.lastrowid
            
            # Memorizza l'allarme attivo
            self._allarmi_attivi[codice_allarme] = allarme_id
            
            return allarme_id

    async def end_allarme(self, codice_allarme: int):
        """Chiude un allarme calcolando la durata"""
        if codice_allarme not in self._allarmi_attivi:
            return
        
        allarme_id = self._allarmi_attivi[codice_allarme]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE allarmi_storico 
                   SET timestamp_fine = CURRENT_TIMESTAMP,
                       durata_secondi = (strftime('%s', 'now') - strftime('%s', timestamp_inizio))
                   WHERE id = ?""",
                (allarme_id,)
            )
            await db.commit()
        
        del self._allarmi_attivi[codice_allarme]

    async def get_allarmi_attivi(self) -> List[Allarme]:
        """Recupera gli allarmi ancora attivi"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM allarmi_storico WHERE timestamp_fine IS NULL"
            ) as cursor:
                rows = await cursor.fetchall()
                return [Allarme(**dict(row)) for row in rows]

    async def get_allarmi_storico(self, limit: int = 100) -> List[Allarme]:
        """Recupera lo storico degli allarmi"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM allarmi_storico ORDER BY timestamp_inizio DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [Allarme(**dict(row)) for row in rows]

    # ========================================================================
    # MONITORAGGIO STATO MACCHINA
    # ========================================================================

    async def process_machine_state(self, machine_data: Dict[str, Any], lavorazione_id: Optional[int] = None):
        """
        Processa lo stato della macchina e registra eventi/allarmi quando cambiano
        
        Args:
            machine_data: Dizionario con tutti i dati della macchina
            lavorazione_id: ID della commessa in lavorazione (se esiste)
        """
        status_flags = machine_data.get('status_flags', {})
        stato_attuale = self._determina_stato_macchina(status_flags)
        ricetta_corrente = machine_data.get('production_data', {}).get('current_recipe', '')
        
        # ====================================================================
        # GESTIONE ALLARMI
        # ====================================================================
        allarmi_attuali = set()
        for i in range(9):
            allarme = machine_data.get('active_alarms', {}).get(f'alarm_{i+1}')
            if allarme and allarme.get('code', 0) != 0:
                codice = allarme['code']
                allarmi_attuali.add(codice)
                
                # Nuovo allarme
                if codice not in self._allarmi_attivi:
                    await self.start_allarme(codice, lavorazione_id)
                    await self.insert_evento_macchina(
                        tipo_evento="ALLARME_INIZIO",
                        stato_macchina=stato_attuale,
                        lavorazione_id=lavorazione_id,
                        dati={'codice_allarme': codice}
                    )
        
        # Chiudi allarmi risolti
        allarmi_risolti = set(self._allarmi_attivi.keys()) - allarmi_attuali
        for codice in allarmi_risolti:
            await self.end_allarme(codice)
            await self.insert_evento_macchina(
                tipo_evento="ALLARME_FINE",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={'codice_allarme': codice}
            )
        
        # ====================================================================
        # PRIMO AVVIO - INIZIALIZZA STATO
        # ====================================================================
        if self._ultimo_stato is None:
            await self.insert_evento_macchina(
                tipo_evento="SISTEMA_AVVIATO",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={'ricetta': ricetta_corrente}
            )
            self._ultimo_stato = {
                'stato': stato_attuale,
                'ricetta': ricetta_corrente,
                'timestamp': machine_data.get('timestamp')
            }
            return
        
        # ====================================================================
        # RILEVA CAMBIAMENTI STATO
        # ====================================================================
        stato_cambiato = stato_attuale != self._ultimo_stato['stato']
        ricetta_cambiata = ricetta_corrente != self._ultimo_stato['ricetta']
        
        if stato_cambiato:
            await self.insert_evento_macchina(
                tipo_evento="CAMBIO_STATO",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'stato_precedente': self._ultimo_stato['stato'],
                    'stato_nuovo': stato_attuale
                }
            )
        
        if ricetta_cambiata:
            await self.insert_evento_macchina(
                tipo_evento="CAMBIO_RICETTA",
                stato_macchina=stato_attuale,
                lavorazione_id=lavorazione_id,
                dati={
                    'ricetta_precedente': self._ultimo_stato['ricetta'],
                    'ricetta_nuova': ricetta_corrente
                }
            )
        
        # ====================================================================
        # AGGIORNA STATO PRECEDENTE
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
    # STATISTICHE E UTILITY
    # ========================================================================

    async def get_commessa_con_dettagli(self, commessa_id: int) -> Optional[Dict[str, Any]]:
        """Recupera una commessa con tutti i dettagli (cliente, ricetta, eventi)"""
        commessa = await self.get_commessa(commessa_id)
        if not commessa:
            return None
        
        cliente = await self.get_cliente(commessa.cliente_id)
        ricetta = await self.get_ricetta(commessa.ricetta_id)
        eventi = await self.get_eventi_commessa(commessa_id, limit=20)
        
        return {
            'commessa': asdict(commessa),
            'cliente': asdict(cliente) if cliente else None,
            'ricetta': asdict(ricetta) if ricetta else None,
            'eventi': [asdict(e) for e in eventi],
            'progresso_percentuale': (commessa.quantita_prodotta / commessa.quantita_richiesta * 100) if commessa.quantita_richiesta > 0 else 0
        }

    async def get_statistiche_commesse(self) -> Dict[str, Any]:
        """Recupera statistiche sulle commesse"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Conteggi per stato
            async with db.execute(
                "SELECT stato, COUNT(*) as count FROM commesse GROUP BY stato"
            ) as cursor:
                rows = await cursor.fetchall()
                stats['per_stato'] = {row[0]: row[1] for row in rows}
            
            # Commesse attive
            async with db.execute(
                "SELECT COUNT(*) FROM commesse WHERE stato IN ('in_lavorazione', 'ricetta_caricata', 'in_attesa')"
            ) as cursor:
                stats['attive'] = (await cursor.fetchone())[0]
            
            # Commesse completate oggi
            async with db.execute(
                """SELECT COUNT(*) FROM commesse 
                   WHERE stato = 'completata' 
                   AND DATE(data_fine_produzione) = DATE('now')"""
            ) as cursor:
                stats['completate_oggi'] = (await cursor.fetchone())[0]
            
            # Quantità totale prodotta oggi
            async with db.execute(
                """SELECT SUM(quantita_prodotta) FROM commesse 
                   WHERE stato = 'completata' 
                   AND DATE(data_fine_produzione) = DATE('now')"""
            ) as cursor:
                result = await cursor.fetchone()
                stats['pezzi_prodotti_oggi'] = result[0] if result[0] else 0
            
            return stats

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
                "SELECT COUNT(*) FROM commesse WHERE stato IN ('in_lavorazione', 'ricetta_caricata')"
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