"""
Servizio per la gestione delle commesse
Gestisce la logica di business per creazione, avvio, monitoraggio e completamento commesse
"""

import asyncio
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date

from database import DatabaseRepository, Commessa
from minipack import MinipackTorreOPCUA


class CommessaValidationError(Exception):
    """Errore di validazione commessa"""
    pass


class CommesseService:
    """
    Servizio per la gestione completa delle commesse
    """
    
    def __init__(
        self, 
        db: DatabaseRepository,
        opc_server: str,
        opc_username: str,
        opc_password: str
    ):
        """
        Inizializza il servizio commesse
        
        Args:
            db: Repository database
            opc_server: URL server OPC UA
            opc_username: Username OPC UA
            opc_password: Password OPC UA
        """
        self.db = db
        self.opc_server = opc_server
        self.opc_username = opc_username
        self.opc_password = opc_password
    
    # ========================================================================
    # VALIDAZIONE E CREAZIONE
    # ========================================================================
    
    async def valida_commessa(
        self, 
        cliente_id: int,
        ricetta_id: int,
        quantita_richiesta: int
    ) -> Tuple[bool, str]:
        """
        Valida i dati di una commessa prima della creazione
        
        Returns:
            (valido: bool, messaggio: str)
        """
        # Verifica cliente esiste
        cliente = await self.db.get_cliente(cliente_id)
        if not cliente:
            return False, f"Cliente con ID {cliente_id} non trovato"
        
        # Verifica ricetta esiste
        ricetta = await self.db.get_ricetta(ricetta_id)
        if not ricetta:
            return False, f"Ricetta con ID {ricetta_id} non trovata"
        
        # Verifica quantità valida
        if quantita_richiesta <= 0:
            return False, "La quantità richiesta deve essere maggiore di zero"
        
        if quantita_richiesta > 1000000:
            return False, "La quantità richiesta sembra troppo alta (max 1.000.000)"
        
        return True, "Validazione OK"
    
    async def crea_commessa(
        self,
        cliente_id: int,
        ricetta_id: int,
        quantita_richiesta: int,
        data_consegna_prevista: Optional[str] = None,
        priorita: str = 'normale',
        note: Optional[str] = None
    ) -> Tuple[bool, int, str]:
        """
        Crea una nuova commessa dopo validazione
        
        Returns:
            (success: bool, commessa_id: int, message: str)
        """
        # Validazione
        valido, messaggio = await self.valida_commessa(cliente_id, ricetta_id, quantita_richiesta)
        if not valido:
            return False, 0, messaggio
        
        # Crea commessa
        commessa = Commessa(
            id=None,
            cliente_id=cliente_id,
            ricetta_id=ricetta_id,
            quantita_richiesta=quantita_richiesta,
            quantita_prodotta=0,
            data_ordine=date.today().isoformat(),
            data_consegna_prevista=data_consegna_prevista,
            stato='in_attesa',
            priorita=priorita,
            note=note
        )
        
        commessa_id = await self.db.create_commessa(commessa)
        
        return True, commessa_id, "Commessa creata con successo"
    
    # ========================================================================
    # CARICAMENTO RICETTA E AVVIO
    # ========================================================================
    
    async def verifica_macchina_pronta(self) -> Tuple[bool, str]:
        """
        Verifica che la macchina sia pronta per caricare una ricetta
        
        Returns:
            (pronta: bool, messaggio: str)
        """
        client = MinipackTorreOPCUA(self.opc_server, self.opc_username, self.opc_password)
        
        try:
            await client.connect()
            
            # Verifica stato macchina
            status_flags = await client.get_status_flags()
            
            if status_flags.get('emergenza'):
                await client.disconnect()
                return False, "Macchina in EMERGENZA - impossibile caricare ricetta"
            
            if not status_flags.get('stop_automatico'):
                await client.disconnect()
                return False, "La macchina deve essere in STOP AUTOMATICO per caricare una ricetta"
            
            await client.disconnect()
            return True, "Macchina pronta"
            
        except Exception as e:
            await client.disconnect()
            return False, f"Errore connessione OPC UA: {str(e)}"
    
    async def carica_ricetta_commessa(
        self,
        commessa_id: int
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Carica la ricetta di una commessa sulla macchina e imposta il contatore lotto
        
        Returns:
            (success: bool, message: str, details: dict)
        """
        # Recupera commessa
        commessa = await self.db.get_commessa(commessa_id)
        if not commessa:
            return False, f"Commessa {commessa_id} non trovata", {}
        
        # Verifica stato commessa
        if commessa.stato not in ['in_attesa']:
            return False, f"Commessa in stato '{commessa.stato}' - impossibile caricare ricetta", {}
        
        # Verifica che non ci sia già una commessa attiva
        commessa_attiva = await self.db.get_commessa_attiva()
        if commessa_attiva and commessa_attiva.id != commessa_id:
            return False, f"C'è già una commessa attiva (ID: {commessa_attiva.id})", {}
        
        # Recupera ricetta
        ricetta = await self.db.get_ricetta(commessa.ricetta_id)
        if not ricetta:
            return False, f"Ricetta ID {commessa.ricetta_id} non trovata", {}
        
        # Verifica macchina pronta
        pronta, msg = await self.verifica_macchina_pronta()
        if not pronta:
            return False, msg, {}
        
        # Carica ricetta sulla macchina
        client = MinipackTorreOPCUA(self.opc_server, self.opc_username, self.opc_password)
        
        try:
            await client.connect()
            
            # Carica ricetta (procedura OPC UA completa)
            success = await client.carica_ricetta(ricetta.nome, timeout=30.0)
            
            if not success:
                await client.disconnect()
                await self.db.update_stato_commessa(
                    commessa_id, 
                    'errore',
                    {'errore': 'Caricamento ricetta fallito'}
                )
                return False, "Caricamento ricetta fallito", {}
            
            # Imposta contatore lotto
            await client.set_contatore_lotto(commessa.quantita_richiesta)
            
            # Verifica che sia stato impostato correttamente
            contatore_impostato = await client.get_contatore_lotto()
            
            await client.disconnect()
            
            # Aggiorna stato commessa
            await self.db.update_stato_commessa(
                commessa_id,
                'ricetta_caricata',
                {
                    'ricetta': ricetta.nome,
                    'contatore_lotto': contatore_impostato,
                    'quantita_richiesta': commessa.quantita_richiesta
                }
            )
            
            # Log evento macchina
            await self.db.insert_evento_macchina(
                tipo_evento="RICETTA_CARICATA_COMMESSA",
                stato_macchina="STOP_AUTOMATICO",
                lavorazione_id=commessa_id,
                dati={
                    'ricetta': ricetta.nome,
                    'contatore_lotto': contatore_impostato,
                    'commessa_id': commessa_id
                }
            )
            
            details = {
                'ricetta_nome': ricetta.nome,
                'contatore_lotto': contatore_impostato,
                'quantita_richiesta': commessa.quantita_richiesta
            }
            
            return True, "Ricetta caricata e contatore impostato con successo", details
            
        except Exception as e:
            await client.disconnect()
            await self.db.update_stato_commessa(
                commessa_id,
                'errore',
                {'errore': str(e)}
            )
            return False, f"Errore durante caricamento: {str(e)}", {}
    
    async def avvia_commessa(self, commessa_id: int) -> Tuple[bool, str]:
        """
        Marca una commessa come 'in_lavorazione' quando la macchina parte
        Questo metodo viene chiamato quando viene rilevato l'avvio macchina
        
        Returns:
            (success: bool, message: str)
        """
        commessa = await self.db.get_commessa(commessa_id)
        if not commessa:
            return False, f"Commessa {commessa_id} non trovata"
        
        if commessa.stato not in ['ricetta_caricata', 'in_attesa']:
            return False, f"Commessa in stato '{commessa.stato}' - impossibile avviare"
        
        await self.db.update_stato_commessa(
            commessa_id,
            'in_lavorazione',
            {'avvio': datetime.now().isoformat()}
        )
        
        return True, "Commessa avviata"
    
    # ========================================================================
    # MONITORAGGIO E AGGIORNAMENTO
    # ========================================================================
    
    async def aggiorna_progresso_commessa(
        self,
        commessa_id: int,
        contatore_lotto_attuale: int
    ) -> bool:
        """
        Aggiorna il progresso di una commessa in base al contatore lotto
        Se raggiunge la quantità richiesta, completa la commessa
        
        Args:
            commessa_id: ID commessa
            contatore_lotto_attuale: Valore attuale del contatore lotto dalla macchina
            
        Returns:
            True se la commessa è stata completata
        """
        commessa = await self.db.get_commessa(commessa_id)
        if not commessa:
            return False
        
        # Calcola quantità prodotta
        quantita_prodotta = commessa.quantita_richiesta - contatore_lotto_attuale
        if quantita_prodotta < 0:
            quantita_prodotta = 0
        
        # Aggiorna quantità
        await self.db.update_quantita_prodotta(commessa_id, quantita_prodotta)
        
        # Verifica se completata
        if quantita_prodotta >= commessa.quantita_richiesta:
            await self.completa_commessa(commessa_id)
            return True
        
        return False
    
    async def completa_commessa(self, commessa_id: int) -> Tuple[bool, str]:
        """
        Marca una commessa come completata
        
        Returns:
            (success: bool, message: str)
        """
        commessa = await self.db.get_commessa(commessa_id)
        if not commessa:
            return False, f"Commessa {commessa_id} non trovata"
        
        if commessa.stato == 'completata':
            return True, "Commessa già completata"
        
        await self.db.update_stato_commessa(
            commessa_id,
            'completata',
            {
                'quantita_finale': commessa.quantita_prodotta,
                'completamento': datetime.now().isoformat()
            }
        )
        
        return True, f"Commessa completata - Prodotti: {commessa.quantita_prodotta}/{commessa.quantita_richiesta} pezzi"
    
    async def annulla_commessa(
        self,
        commessa_id: int,
        motivo: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Annulla una commessa
        
        Args:
            commessa_id: ID commessa
            motivo: Motivo dell'annullamento
            
        Returns:
            (success: bool, message: str)
        """
        commessa = await self.db.get_commessa(commessa_id)
        if not commessa:
            return False, f"Commessa {commessa_id} non trovata"
        
        if commessa.stato in ['completata', 'annullata']:
            return False, f"Impossibile annullare: commessa in stato '{commessa.stato}'"
        
        await self.db.update_stato_commessa(
            commessa_id,
            'annullata',
            {
                'motivo': motivo or 'Non specificato',
                'quantita_prodotta_parziale': commessa.quantita_prodotta
            }
        )
        
        return True, "Commessa annullata"
    
    # ========================================================================
    # RECUPERO INFORMAZIONI
    # ========================================================================
    
    async def get_stato_commessa(self, commessa_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera lo stato completo di una commessa con tutti i dettagli
        
        Returns:
            Dizionario con info complete o None se non trovata
        """
        return await self.db.get_commessa_con_dettagli(commessa_id)
    
    async def get_commesse_attive(self) -> list:
        """
        Recupera tutte le commesse attive (in_attesa, ricetta_caricata, in_lavorazione)
        """
        tutte = await self.db.get_commesse()
        return [
            c for c in tutte 
            if c.stato in ['in_attesa', 'ricetta_caricata', 'in_lavorazione']
        ]
    
    async def get_commesse_da_completare(self) -> list:
        """
        Recupera commesse in lavorazione o con ricetta caricata
        """
        tutte = await self.db.get_commesse()
        return [
            c for c in tutte 
            if c.stato in ['ricetta_caricata', 'in_lavorazione']
        ]


# ============================================================================
# TASK DI MONITORAGGIO BACKGROUND
# ============================================================================

class CommesseMonitoringTask:
    """
    Task in background per monitorare le commesse attive e aggiornarle
    """
    
    def __init__(
        self,
        commesse_service: CommesseService,
        db: DatabaseRepository,
        opc_server: str,
        opc_username: str,
        opc_password: str,
        intervallo: int = 5
    ):
        """
        Inizializza il task di monitoraggio
        
        Args:
            commesse_service: Servizio commesse
            db: Repository database
            opc_server: URL server OPC UA
            opc_username: Username OPC UA
            opc_password: Password OPC UA
            intervallo: Secondi tra ogni controllo
        """
        self.commesse_service = commesse_service
        self.db = db
        self.opc_server = opc_server
        self.opc_username = opc_username
        self.opc_password = opc_password
        self.intervallo = intervallo
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def monitora_loop(self):
        """Loop principale di monitoraggio"""
        while self.running:
            try:
                # Recupera commessa attiva
                commessa_attiva = await self.db.get_commessa_attiva()
                
                if commessa_attiva:
                    # Connetti a OPC UA
                    client = MinipackTorreOPCUA(
                        self.opc_server,
                        self.opc_username,
                        self.opc_password
                    )
                    
                    await client.connect()
                    
                    # Leggi contatore lotto
                    contatore_lotto = await client.get_contatore_lotto()
                    
                    # Verifica se macchina in START (automatico o manuale)
                    status_flags = await client.get_status_flags()
                    macchina_attiva = (
                        status_flags.get('start_automatico') or 
                        status_flags.get('start_manuale')
                    )
                    
                    await client.disconnect()
                    
                    # Se commessa è 'ricetta_caricata' e macchina parte, avvia
                    if commessa_attiva.stato == 'ricetta_caricata' and macchina_attiva:
                        await self.commesse_service.avvia_commessa(commessa_attiva.id)
                    
                    # Aggiorna progresso
                    if commessa_attiva.stato == 'in_lavorazione':
                        completata = await self.commesse_service.aggiorna_progresso_commessa(
                            commessa_attiva.id,
                            contatore_lotto
                        )
                        
                        if completata:
                            print(f"✅ Commessa {commessa_attiva.id} completata!")
                
            except Exception as e:
                print(f"❌ Errore nel monitoraggio commesse: {e}")
            
            await asyncio.sleep(self.intervallo)
    
    def start(self):
        """Avvia il task di monitoraggio"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self.monitora_loop())
            print("✅ Monitoraggio commesse avviato")
    
    def stop(self):
        """Ferma il task di monitoraggio"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
            print("⏹️  Monitoraggio commesse fermato")