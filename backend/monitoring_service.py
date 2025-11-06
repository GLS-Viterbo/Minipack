"""
Servizio di monitoraggio periodico per aggiornamento database
Esegue polling della macchina e aggiorna il database automaticamente
"""

import asyncio
from typing import Optional
from datetime import datetime
from database import DatabaseRepository
from minipack import MinipackTorreOPCUA


class MonitoringService:
    """
    Servizio che monitora periodicamente la macchina e aggiorna il database
    """

    def __init__(
        self,
        opc_server: str,
        opc_username: str,
        opc_password: str,
        db_path: str = "minipack_monitoring.db",
        polling_interval: int = 5
    ):
        """
        Inizializza il servizio di monitoraggio
        
        Args:
            opc_server: URL server OPC UA
            opc_username: Username OPC UA
            opc_password: Password OPC UA
            db_path: Percorso database SQLite
            polling_interval: Intervallo polling in secondi (default: 5)
        """
        self.opc_server = opc_server
        self.opc_username = opc_username
        self.opc_password = opc_password
        self.polling_interval = polling_interval
        
        self.db_repo = DatabaseRepository(db_path)
        self.opc_client: Optional[MinipackTorreOPCUA] = None
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        # ID lavorazione corrente (da impostare quando si avvia una produzione)
        self.current_lavorazione_id: Optional[int] = None

    async def start(self):
        """Avvia il servizio di monitoraggio"""
        if self._running:
            print("⚠️  Servizio di monitoraggio già in esecuzione")
            return
        
        print("🚀 Avvio servizio di monitoraggio...")
        
        # Connetti al database
        await self.db_repo.connect()
        
        # Inizializza client OPC UA
        self.opc_client = MinipackTorreOPCUA(
            self.opc_server,
            self.opc_username,
            self.opc_password
        )
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        
        print(f"✅ Servizio avviato - Polling ogni {self.polling_interval} secondi")

    async def stop(self):
        """Ferma il servizio di monitoraggio"""
        if not self._running:
            return
        
        print("🛑 Arresto servizio di monitoraggio...")
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Disconnetti dal database
        await self.db_repo.disconnect()
        
        print("✅ Servizio arrestato")

    async def _monitoring_loop(self):
        """Loop principale di monitoraggio"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self._running:
            try:
                # Connetti al server OPC UA
                await self.opc_client.connect()
                
                # Recupera tutti i dati dalla macchina
                machine_data = await self._get_machine_data()
                
                # Aggiorna il database con monitoraggio automatico
                await self.db_repo.monitor_machine_state(
                    machine_data,
                    lavorazione_id=self.current_lavorazione_id
                )
                
                # Disconnetti
                await self.opc_client.disconnect()
                
                # Reset contatore errori
                consecutive_errors = 0
                
                # Attendi prima del prossimo ciclo
                await asyncio.sleep(self.polling_interval)
                
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                consecutive_errors += 1
                print(f"❌ Errore nel ciclo di monitoraggio: {e}")
                
                # Se troppi errori consecutivi, aumenta l'intervallo
                if consecutive_errors >= max_consecutive_errors:
                    print(f"⚠️  {consecutive_errors} errori consecutivi - Intervallo aumentato")
                    await asyncio.sleep(self.polling_interval * 3)
                else:
                    await asyncio.sleep(self.polling_interval)
                
                # Assicurati che il client sia disconnesso
                if self.opc_client:
                    try:
                        await self.opc_client.disconnect()
                    except:
                        pass

    async def _get_machine_data(self) -> dict:
        """Recupera tutti i dati dalla macchina in formato dizionario"""
        # Recupera status flags
        status_flags = await self.opc_client.get_status_flags()
        
        # Recupera allarmi
        alarm_codes = await self.opc_client.get_allarmi_attivi()
        alarms = [{'code': code} for code in alarm_codes]
        
        # Costruisce dizionario dati
        return {
            'timestamp': datetime.now().isoformat(),
            'connected': True,
            'status': status_flags,
            'alarms': alarms,
            'recipe': await self.opc_client.get_ricetta_in_lavorazione(),
            'total_pieces': int(await self.opc_client.get_contapezzi_vita()),
            'partial_pieces': int(await self.opc_client.get_contapezzi_parziale()),
            'batch_counter': int(await self.opc_client.get_contatore_lotto()),
            'lateral_bar_temp': await self.opc_client.get_temperatura_barra_laterale(),
            'frontal_bar_temp': await self.opc_client.get_temperatura_barra_frontale(),
            'triangle_position': await self.opc_client.get_posizione_triangolo(),
            'center_sealing_position': await self.opc_client.get_posizione_center_sealing(),
        }

    # ========================================================================
    # METODI DI CONTROLLO LAVORAZIONE
    # ========================================================================

    async def start_lavorazione(self, commessa_id: int):
        """
        Avvia una nuova lavorazione per una commessa
        
        Args:
            commessa_id: ID della commessa da avviare
        """
        # Verifica che la commessa esista
        commessa = await self.db_repo.get_commessa(commessa_id)
        if not commessa:
            raise ValueError(f"Commessa {commessa_id} non trovata")
        
        # Imposta l'ID lavorazione corrente
        self.current_lavorazione_id = commessa_id
        
        # Aggiorna la commessa con data inizio produzione
        commessa.data_inizio_produzione = datetime.now().isoformat()
        await self.db_repo.update_commessa(commessa)
        
        # Registra evento di avvio lavorazione
        await self.db_repo.insert_evento_macchina(
            tipo_evento="AVVIO_LAVORAZIONE",
            lavorazione_id=commessa_id,
            dati={
                'commessa_id': commessa_id,
                'cliente_id': commessa.cliente_id,
                'ricetta_id': commessa.ricetta_id
            }
        )
        
        print(f"📦 Lavorazione avviata per commessa #{commessa_id}")

    async def stop_lavorazione(self):
        """Termina la lavorazione corrente"""
        if not self.current_lavorazione_id:
            print("⚠️  Nessuna lavorazione attiva")
            return
        
        # Recupera la commessa
        commessa = await self.db_repo.get_commessa(self.current_lavorazione_id)
        
        # Aggiorna la commessa con data fine produzione
        commessa.data_fine_produzione = datetime.now().isoformat()
        await self.db_repo.update_commessa(commessa)
        
        # Registra evento di fine lavorazione
        await self.db_repo.insert_evento_macchina(
            tipo_evento="FINE_LAVORAZIONE",
            lavorazione_id=self.current_lavorazione_id,
            dati={
                'commessa_id': self.current_lavorazione_id,
                'quantita_prodotta': commessa.quantita_prodotta
            }
        )
        
        print(f"🏁 Lavorazione terminata per commessa #{self.current_lavorazione_id}")
        print(f"   Quantità prodotta: {commessa.quantita_prodotta}/{commessa.quantita_richiesta}")
        
        # Reset ID lavorazione
        self.current_lavorazione_id = None

    async def update_production_count(self, incremento: int = 1):
        """
        Aggiorna il conteggio produzione per la lavorazione corrente
        
        Args:
            incremento: Numero di pezzi da aggiungere (default: 1)
        """
        if not self.current_lavorazione_id:
            print("⚠️  Nessuna lavorazione attiva")
            return
        
        await self.db_repo.incrementa_quantita_prodotta(
            self.current_lavorazione_id,
            incremento
        )

    # ========================================================================
    # METODI DI INTERROGAZIONE
    # ========================================================================

    async def get_current_status(self) -> dict:
        """Recupera lo stato corrente del servizio"""
        stats = await self.db_repo.get_database_stats()
        
        return {
            'monitoring_active': self._running,
            'polling_interval': self.polling_interval,
            'current_lavorazione_id': self.current_lavorazione_id,
            'database_stats': stats
        }

    async def get_recent_events(self, limit: int = 50) -> list:
        """Recupera gli eventi recenti"""
        return await self.db_repo.get_eventi_macchina(limit=limit)

    async def get_alarm_statistics(self, days: int = 7) -> list:
        """Recupera statistiche allarmi"""
        return await self.db_repo.get_statistiche_allarmi(giorni=days)


# ============================================================================
# ESEMPIO DI UTILIZZO
# ============================================================================

async def main_example():
    """Esempio di utilizzo del servizio di monitoraggio"""
    
    # Configurazione
    OPC_SERVER = "opc.tcp://10.58.156.65:4840"
    OPC_USERNAME = "admin"
    OPC_PASSWORD = "Minipack1"
    
    # Crea il servizio
    service = MonitoringService(
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD,
        polling_interval=5  # Poll ogni 5 secondi
    )
    
    try:
        # Avvia il monitoraggio
        await service.start()
        
        # Simula operazioni...
        
        # 1. Avvia una lavorazione per la commessa #1
        print("\n--- AVVIO LAVORAZIONE ---")
        await service.start_lavorazione(commessa_id=1)
        
        # 2. Lascia monitorare per un po'
        print("\n--- MONITORAGGIO IN CORSO ---")
        await asyncio.sleep(30)
        
        # 3. Simula aggiornamento produzione
        print("\n--- AGGIORNAMENTO PRODUZIONE ---")
        await service.update_production_count(incremento=10)
        
        # 4. Mostra statistiche
        print("\n--- STATISTICHE ---")
        status = await service.get_current_status()
        print(f"Stato servizio: {status}")
        
        # 5. Mostra eventi recenti
        print("\n--- EVENTI RECENTI ---")
        events = await service.get_recent_events(limit=10)
        for event in events:
            print(f"  {event.timestamp} - {event.tipo_evento} - {event.stato_macchina}")
        
        # 6. Termina la lavorazione
        print("\n--- FINE LAVORAZIONE ---")
        await service.stop_lavorazione()
        
        # Continua a monitorare
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\n\n⛔ Interruzione utente")
    
    finally:
        # Ferma il servizio
        await service.stop()


if __name__ == "__main__":
    # Per testare il servizio
    asyncio.run(main_example())