"""
Servizio per il rilevamento automatico delle sessioni di produzione.
Monitora i dati OPC UA e crea/chiude sessioni senza intervento manuale.
Funziona in parallelo al sistema commesse esistente.
"""

from typing import Optional, List, Dict, Any
from database import DatabaseRepository

# Numero di poll consecutivi di inattività prima di chiudere la sessione (15 min a 5s/poll)
IDLE_POLLS_THRESHOLD = 180


class SessionService:
    """
    Rileva e traccia sessioni di produzione automaticamente dal polling OPC UA.

    Trigger di nuova sessione:
    - Cambio ricetta (segnale stabile, affidabile)
    - Bit caricamento_ricetta_ok passa da False a True (stesso recipe ricaricato)
    - Reset manuale contatore (partial_pieces scende rispetto al poll precedente)

    Chiusura sessione:
    - Cambio ricetta (apre immediatamente la nuova)
    - Reset manuale contatore (apre immediatamente la nuova)
    - 5 minuti di fermo (60 poll con macchina in STOP e delta=0)
    """

    def __init__(self, db: DatabaseRepository):
        self.db = db

        # Sessione persistita nel DB (solo dopo il primo pezzo prodotto)
        self._sessione_attiva_id: Optional[int] = None

        # Sessione in attesa: trigger scattato ma ancora 0 pezzi → non ancora nel DB
        self._pending: bool = False
        self._pending_recipe: str = ""
        self._pending_lotto: int = 0
        self._pending_commessa_id: Optional[int] = None

        self._baseline: int = 0
        self._prev_partial: int = 0
        self._prev_recipe: str = ""
        self._prev_caricamento_ok: bool = False
        self._idle_polls: int = 0
        self._first_poll: bool = True

    async def initialize(self) -> None:
        """
        Chiude eventuali sessioni orfane e prepara lo stato al riavvio del server.
        Da chiamare una volta sola dopo la costruzione, prima del primo poll.
        """
        sessione = await self.db.get_sessione_attiva()
        if sessione:
            # La sessione era attiva prima del crash/riavvio: quella produzione è
            # già terminata, va chiusa. La quantità prodotta è già corretta nel DB.
            await self.db.close_sessione(
                sessione['id'],
                contapezzi_fine=sessione['contapezzi_baseline'] + sessione['quantita_prodotta'],
                quantita_prodotta=sessione['quantita_prodotta']
            )

    async def process_poll(
        self,
        machine_data: dict,
        commessa_attiva_id: Optional[int] = None
    ) -> None:
        """
        Punto di ingresso principale. Chiamato ogni 5s da MonitoringService.

        Args:
            machine_data: dizionario dati macchina dal polling OPC UA
            commessa_attiva_id: ID commessa attiva (se presente), per collegare le sessioni
        """
        status_flags: dict = machine_data.get('status_flags', {})
        prod: dict = machine_data.get('production_data', {})

        current_recipe: str = prod.get('current_recipe', '') or ''
        current_partial: int = int(prod.get('partial_pieces', 0))
        current_lotto: int = int(prod.get('batch_counter', 0))
        current_caricamento_ok: bool = bool(status_flags.get('caricamento_ricetta_ok', False))

        machine_running: bool = (
            status_flags.get('start_automatico', False) or
            status_flags.get('start_manuale', False)
        )

        # ----------------------------------------------------------------
        # Primo poll: inizializza lo stato senza scatenare trigger
        # ----------------------------------------------------------------
        if self._first_poll:
            self._prev_recipe = current_recipe
            self._prev_partial = current_partial
            self._prev_caricamento_ok = current_caricamento_ok
            self._first_poll = False
            return

        # ----------------------------------------------------------------
        # Rilevamento trigger di nuova sessione
        # ----------------------------------------------------------------
        recipe_changed = current_recipe != self._prev_recipe and current_recipe != ""
        recipe_ok_edge = current_caricamento_ok and not self._prev_caricamento_ok
        counter_reset = (
            (self._sessione_attiva_id is not None or self._pending) and
            current_partial < self._prev_partial
        )

        start_new = recipe_changed or recipe_ok_edge or counter_reset

        if start_new:
            # Chiudi sessione DB precedente se presente
            if self._sessione_attiva_id is not None:
                quantita_finale = max(0, self._prev_partial - self._baseline)
                await self.db.close_sessione(
                    self._sessione_attiva_id,
                    contapezzi_fine=self._prev_partial,
                    quantita_prodotta=quantita_finale
                )
                self._sessione_attiva_id = None

            # Prepara sessione pending (non ancora nel DB — aspettiamo il primo pezzo)
            if current_recipe:
                self._pending = True
                self._pending_recipe = current_recipe
                self._pending_lotto = current_lotto
                self._pending_commessa_id = commessa_attiva_id
                self._baseline = current_partial
                self._idle_polls = 0
            else:
                self._pending = False

        # ----------------------------------------------------------------
        # Aggiornamento sessione attiva
        # ----------------------------------------------------------------
        quantita = max(0, current_partial - self._baseline)

        if self._pending and quantita > 0:
            # Primo pezzo prodotto: ora creiamo la sessione nel DB
            self._sessione_attiva_id = await self.db.create_sessione(
                ricetta_nome=self._pending_recipe,
                baseline=self._baseline,
                contatore_lotto=self._pending_lotto,
                commessa_id=self._pending_commessa_id
            )
            self._pending = False

        if self._sessione_attiva_id is not None:
            await self.db.update_sessione_quantita(self._sessione_attiva_id, quantita)

            # Rilevamento inattività per chiusura automatica
            delta = current_partial - self._prev_partial
            if not machine_running and delta == 0:
                self._idle_polls += 1
            else:
                self._idle_polls = 0

            if self._idle_polls >= IDLE_POLLS_THRESHOLD:
                await self.db.close_sessione(
                    self._sessione_attiva_id,
                    contapezzi_fine=current_partial,
                    quantita_prodotta=quantita
                )
                self._sessione_attiva_id = None
                self._pending = False
                self._idle_polls = 0

        # ----------------------------------------------------------------
        # Aggiorna stato precedente per il prossimo ciclo
        # ----------------------------------------------------------------
        self._prev_recipe = current_recipe
        self._prev_partial = current_partial
        self._prev_caricamento_ok = current_caricamento_ok

    # ====================================================================
    # METODI DI QUERY (usati dagli endpoint API)
    # ====================================================================

    async def get_sessione_attiva(self) -> Optional[Dict[str, Any]]:
        """Restituisce la sessione attualmente in corso, o None."""
        return await self.db.get_sessione_attiva()

    async def get_sessione(self, sessione_id: int) -> Optional[Dict[str, Any]]:
        """Restituisce una sessione per ID."""
        return await self.db.get_sessione(sessione_id)

    async def get_sessioni(
        self,
        limit: int = 50,
        data_inizio: Optional[str] = None,
        data_fine: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Restituisce le sessioni passate con filtri opzionali."""
        return await self.db.get_sessioni(limit=limit, data_inizio=data_inizio, data_fine=data_fine)
