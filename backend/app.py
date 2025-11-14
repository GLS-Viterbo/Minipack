"""
REST API per monitoraggio macchina MinipackTorre con gestione completa commesse
Versione 3.0 - Integrazione completa sistema commesse
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import asyncio
from contextlib import asynccontextmanager
import json
from fastapi.responses import StreamingResponse, Response
from export_service import ExportService

from minipack import MinipackTorreOPCUA
from database import DatabaseRepository, Cliente, Ricetta, Commessa
from monitoring_service import MonitoringService
from commesse_service import CommesseService, CommesseMonitoringTask

# Configurazione server OPC UA
OPC_SERVER = "opc.tcp://10.58.156.65:4840"
OPC_USERNAME = "admin"
OPC_PASSWORD = "Minipack1"

# Servizi globali
monitoring_service: Optional[MonitoringService] = None
commesse_service: Optional[CommesseService] = None
commesse_monitoring_task: Optional[CommesseMonitoringTask] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione lifecycle dell'applicazione"""
    global monitoring_service, commesse_service, commesse_monitoring_task
    
    # Startup
    print("🚀 Avvio servizi...")
    
    # Database
    db = DatabaseRepository()
    await db.connect()
    
    # Servizio monitoraggio macchina
    monitoring_service = MonitoringService(
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD,
        polling_interval=5
    )
    await monitoring_service.start()
    print("✅ Servizio monitoraggio macchina avviato")
    
    # Servizio gestione commesse
    commesse_service = CommesseService(
        db=db,
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD
    )
    print("✅ Servizio gestione commesse inizializzato")
    
    # Task monitoraggio commesse
    commesse_monitoring_task = CommesseMonitoringTask(
        commesse_service=commesse_service,
        db=db,
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD,
        intervallo=5
    )
    commesse_monitoring_task.start()
    print("✅ Task monitoraggio commesse avviato")
    
    yield
    
    # Shutdown
    print("🛑 Arresto servizi...")
    if monitoring_service:
        await monitoring_service.stop()
    if commesse_monitoring_task:
        commesse_monitoring_task.stop()
    await db.disconnect()


app = FastAPI(
    title="MinipackTorre API - Gestione Commesse",
    description="API completa per monitoraggio macchina e gestione commesse di produzione",
    version="3.0.0",
    lifespan=lifespan
)

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELLI PYDANTIC
# ============================================================================

class AlarmInfo(BaseModel):
    code: int
    message: str


class MachineStatus(BaseModel):
    stop_manuale: bool
    start_manuale: bool
    stop_automatico: bool
    start_automatico: bool
    emergenza: bool
    status_text: str


class MachineData(BaseModel):
    timestamp: str
    connected: bool
    software_name: str
    software_version: str
    status: MachineStatus
    alarms: List[AlarmInfo]
    has_alarms: bool
    recipe: str
    total_pieces: int
    partial_pieces: int
    batch_counter: int
    lateral_bar_temp: float
    frontal_bar_temp: float
    triangle_position: float
    center_sealing_position: float


# Modelli Cliente
class ClienteCreate(BaseModel):
    nome: str
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    nome: str
    partita_iva: Optional[str]
    codice_fiscale: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


# Modelli Ricetta
class RicettaCreate(BaseModel):
    nome: str
    descrizione: Optional[str] = None


class RicettaResponse(BaseModel):
    id: int
    nome: str
    descrizione: Optional[str]


# Modelli Commessa
class CommessaCreate(BaseModel):
    cliente_id: int
    ricetta_id: int
    quantita_richiesta: int
    data_consegna_prevista: Optional[str] = None
    priorita: str = 'normale'
    note: Optional[str] = None


class CommessaResponse(BaseModel):
    id: int
    cliente_id: int
    ricetta_id: int
    quantita_richiesta: int
    quantita_prodotta: int
    data_ordine: str
    data_consegna_prevista: Optional[str]
    data_inizio_produzione: Optional[str]
    data_fine_produzione: Optional[str]
    stato: str
    priorita: str
    note: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


# Modelli richieste specifiche
class LoadRecipeRequest(BaseModel):
    recipe_name: str


class LoadRecipeResponse(BaseModel):
    success: bool
    message: str
    recipe_name: Optional[str] = None


class CaricaRicettaCommessaRequest(BaseModel):
    commessa_id: int


class AvviaCommessaResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def get_machine_data() -> MachineData:
    """Recupera tutti i dati della macchina"""
    client = MinipackTorreOPCUA(OPC_SERVER, OPC_USERNAME, OPC_PASSWORD)

    ALARM_MESSAGES = {
        1: "EMERGENZA ATTIVA",
        2: "RIPARI APERTI",
        3: "BYPASS SICUREZZA RIPARI",
        6: "ALTEZZA MASSIMA TRIANGOLO",
        10: "MACCHINA IN RISCALDAMENTO",
        11: "AVVOLGITORE PIENO",
        12: "SVOLGITORE: BOBINA IN ESAURIMENTO",
        13: "SVOLGITORE: FILM ESAURITO",
        14: "NASTRI NON DISTANZIATI",
        15: "ERRORE CIRCUITO TEMPERATURE",
        17: "SVOLGITORE: TIMEOUT",
        20: "INVERTER: ERRORE INVERTER",
        22: "MANUTENZIONE IN CORSO",
        23: "NASTRO DI CARICO VUOTO",
        25: "NUMERO LOTTO RAGGIUNTO",
        26: "AVVOLGITORE: ROTTURA FILM",
        27: "FOTOCELLULE TIMEOUT",
        29: "AVVICINAMENTO NASTRO: ERRORE INVERTER",
        33: "CENTER SEALING: FINECORSA ALTO",
        34: "SVOLGITORE FUORI POSIZIONE",
        35: "TRIANGOLO: ERRORE MOVIMENTAZIONE",
        41: "HOMING: TIMEOUT",
        42: "HOMING: PROCEDURA FALLITA",
        46: "CENTER SEALING: ERRORE MOVIMENTAZIONE",
        48: "ERRORE STAMPANTE",
        49: "CENTER SEALING: BLOCCO MOVIMENTO",
        50: "TRIANGOLO: BLOCCO MOVIMENTO",
        51: "NASTRO DI CARICO: NON DISPONIBILE",
        52: "NASTRO DI SCARICO: NON DISPONIBILE",
        54: "BARRA SALDANTE: TIMEOUT MOVIMENTO",
        55: "BARRA SALDANTE: PRESENZA OSTACOLO",
        73: "LINEA A VALLE: MANCA CONSENSO DA LINEA",
        74: "BARRA SALDANTE NODO CAN ASSENTE",
        75: "INVERTER NODO CAN ASSENTE",
        76: "CXCAN1 NODO CAN ASSENTE",
        77: "CXCAN2 NODO CAN ASSENTE",
        78: "ALLARME BARRA SALDANTE",
        79: "AVVICINAMENTO NASTRO: TIMEOUT",
        80: "INVERTER: TIMEOUT START",
    }
    
    try:
        await client.connect()
        
        # Recupera stato
        status_flags = await client.get_status_flags()
        
        # Determina testo stato
        if status_flags['emergenza']:
            status_text = "EMERGENZA"
        elif status_flags['start_automatico']:
            status_text = "START AUTOMATICO"
        elif status_flags['start_manuale']:
            status_text = "START MANUALE"
        elif status_flags['stop_automatico']:
            status_text = "STOP AUTOMATICO"
        elif status_flags['stop_manuale']:
            status_text = "STOP MANUALE"
        else:
            status_text = "SCONOSCIUTO"
        
        # Recupera allarmi
        alarm_codes = await client.get_allarmi_attivi()

        alarms = [
            AlarmInfo(
                code=code,
                message=ALARM_MESSAGES.get(code, f"A{code:03d} - Allarme sconosciuto")
            )
            for code in alarm_codes
        ]
        
        # Componi risposta
        data = MachineData(
            timestamp=datetime.now().isoformat(),
            connected=True,
            software_name=await client.get_nome_software(),
            software_version=await client.get_versione_software(),
            status=MachineStatus(
                stop_manuale=status_flags['stop_manuale'],
                start_manuale=status_flags['start_manuale'],
                stop_automatico=status_flags['stop_automatico'],
                start_automatico=status_flags['start_automatico'],
                emergenza=status_flags['emergenza'],
                status_text=status_text
            ),
            alarms=alarms,
            has_alarms=len(alarms) > 0,
            recipe=await client.get_ricetta_in_lavorazione(),
            total_pieces=await client.get_contapezzi_vita(),
            partial_pieces=await client.get_contapezzi_parziale(),
            batch_counter=await client.get_contatore_lotto(),
            lateral_bar_temp=await client.get_temperatura_barra_laterale(),
            frontal_bar_temp=await client.get_temperatura_barra_frontale(),
            triangle_position=await client.get_posizione_triangolo(),
            center_sealing_position=await client.get_posizione_center_sealing(),
        )
        
        await client.disconnect()
        return data
        
    except Exception as e:
        await client.disconnect()
        print(e)
        raise HTTPException(status_code=500, detail=f"Errore connessione OPC UA: {str(e)}")


# ============================================================================
# ENDPOINT ROOT E HEALTH
# ============================================================================

@app.get("/")
async def root():
    """Endpoint radice con informazioni API"""
    return {
        "name": "MinipackTorre API - Gestione Commesse",
        "version": "3.0.0",
        "description": "API completa per monitoraggio macchina e gestione commesse di produzione",
        "endpoints": {
            "machine": {
                "/data": "GET - Dati real-time macchina",
                "/health": "GET - Stato servizi",
                "/reset-alarms": "POST - Reset allarmi"
            },
            "clienti": {
                "/clienti": "GET - Lista clienti / POST - Crea cliente",
                "/clienti/{id}": "GET - Dettaglio cliente / DELETE - Elimina cliente"
            },
            "ricette": {
                "/ricette": "GET - Lista ricette / POST - Crea ricetta",
                "/ricette/{id}": "DELETE - Elimina ricetta"
            },
            "commesse": {
                "/commesse": "GET - Lista commesse / POST - Crea commessa",
                "/commesse/{id}": "GET - Dettaglio commessa completo",
                "/commesse/{id}/carica-ricetta": "POST - Carica ricetta e imposta contatore",
                "/commesse/{id}/annulla": "POST - Annulla commessa",
                "/commesse/attive": "GET - Lista commesse attive",
                "/commesse/statistiche": "GET - Statistiche commesse"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check completo dell'API e servizi"""
    db = DatabaseRepository()
    await db.connect()
    db_stats = await db.get_database_stats()
    await db.disconnect()
    
    status = await monitoring_service.get_current_status()
    
    return {
        "api_status": "ok",
        "services": {
            "monitoring_active": status['monitoring_active'],
            "commesse_monitoring_active": commesse_monitoring_task.running if commesse_monitoring_task else False
        },
        "database": db_stats,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# ENDPOINT MACCHINA
# ============================================================================

@app.get("/data", response_model=MachineData)
async def get_data():
    """Recupera tutti i dati della macchina in tempo reale"""
    return await get_machine_data()


@app.post("/reset-alarms")
async def reset_alarms():
    """Esegue il reset degli allarmi sulla macchina"""
    client = MinipackTorreOPCUA(OPC_SERVER, OPC_USERNAME, OPC_PASSWORD)
    
    try:
        await client.connect()
        await client.reset_allarmi()
        await client.disconnect()
        
        return {
            "success": True,
            "message": "Reset allarmi eseguito con successo"
        }
        
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore durante il reset allarmi: {str(e)}")


# ============================================================================
# ENDPOINT CLIENTI
# ============================================================================

@app.get("/clienti", response_model=List[ClienteResponse])
async def get_clienti():
    """Recupera tutti i clienti"""
    db = DatabaseRepository()
    await db.connect()
    clienti = await db.get_clienti()
    await db.disconnect()
    
    return [ClienteResponse(
        id=c.id,
        nome=c.nome,
        partita_iva=c.partita_iva,
        codice_fiscale=c.codice_fiscale,
        created_at=c.created_at,
        updated_at=c.updated_at
    ) for c in clienti]


@app.post("/clienti", response_model=ClienteResponse)
async def create_cliente(cliente: ClienteCreate):
    """Crea un nuovo cliente"""
    db = DatabaseRepository()
    await db.connect()
    
    new_cliente = Cliente(
        id=None,
        nome=cliente.nome,
        partita_iva=cliente.partita_iva,
        codice_fiscale=cliente.codice_fiscale
    )
    
    cliente_id = await db.create_cliente(new_cliente)
    created = await db.get_cliente(cliente_id)
    await db.disconnect()
    
    return ClienteResponse(
        id=created.id,
        nome=created.nome,
        partita_iva=created.partita_iva,
        codice_fiscale=created.codice_fiscale,
        created_at=created.created_at,
        updated_at=created.updated_at
    )


@app.get("/clienti/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(cliente_id: int):
    """Recupera un cliente per ID"""
    db = DatabaseRepository()
    await db.connect()
    cliente = await db.get_cliente(cliente_id)
    await db.disconnect()
    
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    return ClienteResponse(
        id=cliente.id,
        nome=cliente.nome,
        partita_iva=cliente.partita_iva,
        codice_fiscale=cliente.codice_fiscale,
        created_at=cliente.created_at,
        updated_at=cliente.updated_at
    )


@app.delete("/clienti/{cliente_id}")
async def delete_cliente(cliente_id: int):
    """Elimina un cliente"""
    db = DatabaseRepository()
    await db.connect()
    
    cliente = await db.get_cliente(cliente_id)
    if not cliente:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    try:
        await db.delete_cliente(cliente_id)
        await db.disconnect()
        return {
            "success": True,
            "message": f"Cliente '{cliente.nome}' eliminato con successo"
        }
    except Exception as e:
        await db.disconnect()
        raise HTTPException(
            status_code=400, 
            detail="Impossibile eliminare: il cliente potrebbe avere commesse associate"
        )


# ============================================================================
# ENDPOINT RICETTE
# ============================================================================

@app.get("/ricette", response_model=List[RicettaResponse])
async def get_ricette():
    """Recupera tutte le ricette"""
    db = DatabaseRepository()
    await db.connect()
    ricette = await db.get_ricette()
    await db.disconnect()
    
    return [RicettaResponse(
        id=r.id,
        nome=r.nome,
        descrizione=r.descrizione
    ) for r in ricette]


@app.post("/ricette", response_model=RicettaResponse)
async def create_ricetta(ricetta: RicettaCreate):
    """Crea una nuova ricetta"""
    db = DatabaseRepository()
    await db.connect()
    
    new_ricetta = Ricetta(
        id=None,
        nome=ricetta.nome,
        descrizione=ricetta.descrizione
    )
    
    ricetta_id = await db.create_ricetta(new_ricetta)
    created = await db.get_ricetta(ricetta_id)
    await db.disconnect()
    
    return RicettaResponse(
        id=created.id,
        nome=created.nome,
        descrizione=created.descrizione
    )

@app.post("/commesse/{commessa_id}/interrompi")
async def interrompi_commessa(commessa_id: int, motivo: Optional[str] = None):
    """
    Interrompe una commessa in lavorazione
    
    Questo endpoint permette di fermare una commessa che è già in produzione.
    NOTA: Non ferma fisicamente la macchina (deve essere fermata manualmente dall'operatore).
    Cambia solo lo stato della commessa nel sistema per liberare il gestionale.
    
    Args:
        commessa_id: ID della commessa da interrompere
        motivo: Motivo dell'interruzione (opzionale)
    
    Returns:
        Messaggio di conferma
    """
    db = DatabaseRepository()
    await db.connect()
    
    commessa = await db.get_commessa(commessa_id)
    if not commessa:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Commessa non trovata")
    
    try:
        # Aggiorna stato a "annullata" con informazioni sull'interruzione
        dati_extra = {
            'interruzione': datetime.now().isoformat(),
            'quantita_prodotta_al_momento': commessa.quantita_prodotta,
            'motivo': motivo or 'Interruzione manuale',
            'tipo_terminazione': 'interrotta_durante_lavorazione'
        }
        
        await db.update_stato_commessa(
            commessa_id,
            'annullata',  # Usiamo 'annullata' per indicare terminazione anticipata
            dati_extra
        )
        
        # Registra evento di interruzione
        await db.insert_evento_commessa(
            commessa_id=commessa_id,
            tipo_evento="INTERRUZIONE_LAVORAZIONE",
            dettagli=json.dumps({
                'quantita_prodotta': commessa.quantita_prodotta,
                'quantita_richiesta': commessa.quantita_richiesta,
                'motivo': motivo or 'Interruzione manuale'
            })
        )
        
        # Log evento macchina
        await db.insert_evento_macchina(
            tipo_evento="COMMESSA_INTERROTTA",
            stato_macchina="IN_LAVORAZIONE",  # Lo stato fisico della macchina
            lavorazione_id=commessa_id,
            dati={
                'commessa_id': commessa_id,
                'motivo': motivo or 'Interruzione manuale',
                'pezzi_prodotti': commessa.quantita_prodotta
            }
        )
        
        await db.disconnect()
        
        return {
            "success": True,
            "message": f"Commessa interrotta. Prodotti: {commessa.quantita_prodotta}/{commessa.quantita_richiesta} pezzi",
            "note": "ATTENZIONE: La macchina deve essere fermata manualmente dall'operatore. Il sistema è ora libero per caricare una nuova ricetta."
        }
        
    except Exception as e:
        await db.disconnect()
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'interruzione: {str(e)}"
        )


@app.delete("/ricette/{ricetta_id}")
async def delete_ricetta(ricetta_id: int):
    """Elimina una ricetta"""
    db = DatabaseRepository()
    await db.connect()
    
    ricetta = await db.get_ricetta(ricetta_id)
    if not ricetta:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Ricetta non trovata")
    
    try:
        await db.delete_ricetta(ricetta_id)
        await db.disconnect()
        return {
            "success": True,
            "message": f"Ricetta '{ricetta.nome}' eliminata con successo"
        }
    except Exception as e:
        await db.disconnect()
        raise HTTPException(
            status_code=400, 
            detail="Impossibile eliminare: la ricetta potrebbe essere utilizzata in commesse"
        )


# ============================================================================
# ENDPOINT COMMESSE - PRINCIPALI
# ============================================================================

@app.get("/commesse", response_model=List[CommessaResponse])
async def get_commesse(stato: Optional[str] = None):
    """
    Recupera le commesse, opzionalmente filtrate per stato
    
    Query params:
        stato: Filtra per stato ('in_attesa', 'ricetta_caricata', 'in_lavorazione', 'completata', 'annullata', 'errore')
    """
    db = DatabaseRepository()
    await db.connect()
    commesse = await db.get_commesse(filtro_stato=stato)
    await db.disconnect()
    
    return [CommessaResponse(
        id=c.id,
        cliente_id=c.cliente_id,
        ricetta_id=c.ricetta_id,
        quantita_richiesta=c.quantita_richiesta,
        quantita_prodotta=c.quantita_prodotta,
        data_ordine=c.data_ordine,
        data_consegna_prevista=c.data_consegna_prevista,
        data_inizio_produzione=c.data_inizio_produzione,
        data_fine_produzione=c.data_fine_produzione,
        stato=c.stato,
        priorita=c.priorita,
        note=c.note,
        created_at=c.created_at,
        updated_at=c.updated_at
    ) for c in commesse]


@app.get("/commesse/attive", response_model=List[CommessaResponse])
async def get_commesse_attive():
    """Recupera solo le commesse attive (in_attesa, ricetta_caricata, in_lavorazione)"""
    commesse = await commesse_service.get_commesse_attive()
    
    return [CommessaResponse(
        id=c.id,
        cliente_id=c.cliente_id,
        ricetta_id=c.ricetta_id,
        quantita_richiesta=c.quantita_richiesta,
        quantita_prodotta=c.quantita_prodotta,
        data_ordine=c.data_ordine,
        data_consegna_prevista=c.data_consegna_prevista,
        data_inizio_produzione=c.data_inizio_produzione,
        data_fine_produzione=c.data_fine_produzione,
        stato=c.stato,
        priorita=c.priorita,
        note=c.note,
        created_at=c.created_at,
        updated_at=c.updated_at
    ) for c in commesse]


@app.post("/commesse", response_model=CommessaResponse)
async def create_commessa(commessa: CommessaCreate):
    """
    Crea una nuova commessa
    
    Validazioni:
    - Cliente deve esistere
    - Ricetta deve esistere
    - Quantità deve essere > 0
    """
    success, commessa_id, message = await commesse_service.crea_commessa(
        cliente_id=commessa.cliente_id,
        ricetta_id=commessa.ricetta_id,
        quantita_richiesta=commessa.quantita_richiesta,
        data_consegna_prevista=commessa.data_consegna_prevista,
        priorita=commessa.priorita,
        note=commessa.note
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    db = DatabaseRepository()
    await db.connect()
    created = await db.get_commessa(commessa_id)
    await db.disconnect()
    
    return CommessaResponse(
        id=created.id,
        cliente_id=created.cliente_id,
        ricetta_id=created.ricetta_id,
        quantita_richiesta=created.quantita_richiesta,
        quantita_prodotta=created.quantita_prodotta,
        data_ordine=created.data_ordine,
        data_consegna_prevista=created.data_consegna_prevista,
        data_inizio_produzione=created.data_inizio_produzione,
        data_fine_produzione=created.data_fine_produzione,
        stato=created.stato,
        priorita=created.priorita,
        note=created.note,
        created_at=created.created_at,
        updated_at=created.updated_at
    )


@app.get("/commesse/{commessa_id}")
async def get_commessa_dettagli(commessa_id: int):
    """
    Recupera dettagli completi di una commessa
    Include: dati commessa, cliente, ricetta, eventi, progresso
    """
    dettagli = await commesse_service.get_stato_commessa(commessa_id)
    
    if not dettagli:
        raise HTTPException(status_code=404, detail="Commessa non trovata")
    
    return dettagli


# ============================================================================
# ENDPOINT COMMESSE - OPERAZIONI
# ============================================================================

@app.post("/commesse/{commessa_id}/carica-ricetta", response_model=AvviaCommessaResponse)
async def carica_ricetta_commessa(commessa_id: int):
    """
    Carica la ricetta di una commessa sulla macchina e imposta il contatore lotto
    
    Prerequisiti:
    - Commessa in stato 'in_attesa'
    - Macchina in STOP AUTOMATICO
    - Nessun'altra commessa attiva
    
    Operazioni eseguite:
    1. Carica ricetta tramite protocollo OPC UA
    2. Imposta contatore lotto con quantità richiesta
    3. Aggiorna stato commessa a 'ricetta_caricata'
    4. Logga evento nel database
    """
    success, message, details = await commesse_service.carica_ricetta_commessa(commessa_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return AvviaCommessaResponse(
        success=success,
        message=message,
        details=details
    )


@app.post("/commesse/{commessa_id}/annulla")
async def annulla_commessa(commessa_id: int, motivo: Optional[str] = None):
    """
    Annulla una commessa
    
    La commessa viene marcata come 'annullata' e non può più essere riavviata
    """
    success, message = await commesse_service.annulla_commessa(commessa_id, motivo)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": success,
        "message": message
    }


# ============================================================================
# ENDPOINT STATISTICHE
# ============================================================================

@app.get("/commesse/statistiche")
async def get_statistiche_commesse():
    """
    Recupera statistiche sulle commesse
    
    Ritorna:
    - Conteggi per stato
    - Commesse attive
    - Commesse completate oggi
    - Pezzi prodotti oggi
    """
    db = DatabaseRepository()
    await db.connect()
    stats = await db.get_statistiche_commesse()
    await db.disconnect()
    
    return stats


@app.get("/statistiche")
async def get_statistiche_generali():
    """Statistiche generali del sistema"""
    db = DatabaseRepository()
    await db.connect()
    
    db_stats = await db.get_database_stats()
    commesse_stats = await db.get_statistiche_commesse()
    
    await db.disconnect()
    
    return {
        "database": db_stats,
        "commesse": commesse_stats,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# ENDPOINT EXPORT E REPORTING
# ============================================================================

@app.get("/export/produzione")
async def export_dati_produzione(
    data_inizio: str,
    data_fine: str,
    formato: str = "json"
):
    """
    Esporta dati di produzione per periodo specificato
    
    Query params:
        data_inizio: Data inizio periodo (YYYY-MM-DD)
        data_fine: Data fine periodo (YYYY-MM-DD)
        formato: Formato export (json, csv, excel)
        
    Returns:
        File nel formato richiesto
    """
    db = DatabaseRepository()
    await db.connect()
    
    export_service = ExportService(db)
    
    try:
        if formato.lower() == "csv":
            csv_data = await export_service.export_csv(data_inizio, data_fine)
            await db.disconnect()
            
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=produzione_{data_inizio}_{data_fine}.csv"
                }
            )
        
        elif formato.lower() == "excel":
            excel_data = await export_service.export_excel(data_inizio, data_fine)
            await db.disconnect()
            
            return StreamingResponse(
                excel_data,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=produzione_{data_inizio}_{data_fine}.xlsx"
                }
            )
        
        elif formato.lower() == "json":
            json_data = await export_service.export_json(data_inizio, data_fine, include_kpi=True)
            await db.disconnect()
            
            return Response(
                content=json_data,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename=produzione_{data_inizio}_{data_fine}.json"
                }
            )
        
        else:
            await db.disconnect()
            raise HTTPException(
                status_code=400, 
                detail=f"Formato '{formato}' non supportato. Usare: json, csv, excel"
            )
    
    except Exception as e:
        await db.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore durante export: {str(e)}")


@app.get("/report/kpi")
async def get_kpi_report(
    data_inizio: str,
    data_fine: str
):
    """
    Recupera report KPI per il periodo specificato
    
    Query params:
        data_inizio: Data inizio periodo (YYYY-MM-DD)
        data_fine: Data fine periodo (YYYY-MM-DD)
        
    Returns:
        JSON con KPI calcolati
    """
    db = DatabaseRepository()
    await db.connect()
    
    export_service = ExportService(db)
    
    try:
        kpi = await export_service.calcola_kpi(data_inizio, data_fine)
        await db.disconnect()
        return kpi
    
    except Exception as e:
        await db.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore calcolo KPI: {str(e)}")


@app.get("/report/dati-completi")
async def get_dati_completi_produzione(
    data_inizio: str,
    data_fine: str
):
    """
    Recupera tutti i dati di produzione per il periodo specificato
    Include: commesse, allarmi, eventi
    
    Query params:
        data_inizio: Data inizio periodo (YYYY-MM-DD)
        data_fine: Data fine periodo (YYYY-MM-DD)
        
    Returns:
        JSON con dati completi
    """
    db = DatabaseRepository()
    await db.connect()
    
    export_service = ExportService(db)
    
    try:
        dati = await export_service.get_dati_produzione(data_inizio, data_fine)
        await db.disconnect()
        return dati
    
    except Exception as e:
        await db.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore recupero dati: {str(e)}")

# ============================================================================
# AVVIO APPLICAZIONE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )