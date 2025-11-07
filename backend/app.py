"""
REST API per monitoraggio macchina MinipackTorre con integrazione database
Estende l'API esistente con endpoint per gestione commesse e statistiche
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import asyncio
from contextlib import asynccontextmanager

from minipack import MinipackTorreOPCUA
from database import DatabaseRepository, Cliente, Ricetta, Commessa
from monitoring_service import MonitoringService

# Configurazione server OPC UA
OPC_SERVER = "opc.tcp://10.58.156.65:4840"
OPC_USERNAME = "admin"
OPC_PASSWORD = "Minipack1"

# Servizio di monitoraggio globale
monitoring_service: Optional[MonitoringService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione lifecycle dell'applicazione"""
    global monitoring_service
    
    # Startup
    print("🚀 Avvio servizio di monitoraggio...")
    monitoring_service = MonitoringService(
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD,
        polling_interval=5
    )
    await monitoring_service.start()
    
    yield
    
    # Shutdown
    print("🛑 Arresto servizio di monitoraggio...")
    if monitoring_service:
        await monitoring_service.stop()


app = FastAPI(
    title="MinipackTorre API with Database",
    description="API per monitoraggio real-time macchina confezionatrice con tracciabilità produzione",
    version="2.0.0",
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


class ClienteCreate(BaseModel):
    nome: str
    partita_iva: Optional[str] = None
    codice_fiscale: Optional[str] = None


class ClienteResponse(BaseModel):
    id: int
    nome: str
    partita_iva: Optional[str]
    codice_fiscale: Optional[str]
    created_at: str
    updated_at: str


class RicettaCreate(BaseModel):
    nome: str
    descrizione: Optional[str] = None


class RicettaResponse(BaseModel):
    id: int
    nome: str
    descrizione: Optional[str]


class CommessaCreate(BaseModel):
    cliente_id: int
    ricetta_id: int
    quantita_richiesta: int
    data_ordine: str
    data_consegna_prevista: Optional[str] = None


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
    created_at: str
    updated_at: str


class StartLavorazioneRequest(BaseModel):
    commessa_id: int


class LoadRecipeRequest(BaseModel):
    recipe_name: str


class LoadRecipeResponse(BaseModel):
    success: bool
    message: str
    recipe_name: str


# Dizionario messaggi allarmi
ALARM_MESSAGES = {
    1: "EMERGENZA ATTIVA",
    2: "RIPARI APERTI",
    3: "BYPASS SICUREZZA RIPARI",
    6: "ALTEZZA MASSIMA TRIANGOLO",
    10: "MACCHINA IN RISCALDAMENTO",
    11: "AVVOLGITORE PIENO",
    12: "BOBINA IN ESAURIMENTO",
    13: "FILM ESAURITO",
    14: "NASTRI NON DISTANZIATI",
    15: "ERRORE CIRCUITO TEMPERATURE",
    17: "SVOLGITORE TIMEOUT",
    20: "INVERTER ERRORE",
    22: "MANUTENZIONE IN CORSO",
    23: "NASTRO CARICO VUOTO",
    25: "NUMERO LOTTO RAGGIUNTO",
    26: "ROTTURA FILM",
    27: "FOTOCELLULE TIMEOUT",
    29: "AVVICINAMENTO NASTRO ERRORE",
    33: "CENTER SEALING FINECORSA ALTO",
    34: "SVOLGITORE FUORI POSIZIONE",
    35: "TRIANGOLO ERRORE MOVIMENTAZIONE",
    41: "HOMING TIMEOUT",
    42: "HOMING FALLITO",
    46: "CENTER SEALING ERRORE",
    48: "ERRORE STAMPANTE",
    49: "CENTER SEALING BLOCCO",
    50: "TRIANGOLO BLOCCO",
    51: "NASTRO CARICO NON DISPONIBILE",
    52: "NASTRO SCARICO NON DISPONIBILE",
    54: "BARRA SALDANTE TIMEOUT",
    55: "BARRA SALDANTE OSTACOLO",
    73: "LINEA VALLE MANCA CONSENSO",
    74: "BARRA SALDANTE CAN ASSENTE",
    75: "INVERTER CAN ASSENTE",
    76: "CXCAN1 ASSENTE",
    77: "CXCAN2 ASSENTE",
    78: "ALLARME BARRA SALDANTE",
    79: "AVVICINAMENTO NASTRO TIMEOUT",
    80: "INVERTER TIMEOUT START"
}


def get_status_text(status_flags: dict) -> str:
    """Determina il testo dello stato macchina"""
    if status_flags['emergenza']:
        return "EMERGENZA"
    elif status_flags['start_automatico']:
        return "IN PRODUZIONE (AUTO)"
    elif status_flags['start_manuale']:
        return "IN MARCIA (MANUALE)"
    elif status_flags['stop_automatico']:
        return "PRONTA (STOP AUTO)"
    elif status_flags['stop_manuale']:
        return "FERMATA (STOP MANUALE)"
    else:
        return "STATO SCONOSCIUTO"


async def get_machine_data() -> MachineData:
    """Recupera tutti i dati dalla macchina"""
    client = MinipackTorreOPCUA(OPC_SERVER, OPC_USERNAME, OPC_PASSWORD)
    
    try:
        await client.connect()
        
        # Recupera status flags
        status_flags = await client.get_status_flags()
        
        # Recupera allarmi
        alarm_codes = await client.get_allarmi_attivi()
        alarms = [
            AlarmInfo(
                code=code,
                message=ALARM_MESSAGES.get(code, f"Allarme sconosciuto (codice {code})")
            )
            for code in alarm_codes
        ]
        
        # Costruisce la risposta
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
                status_text=get_status_text(status_flags)
            ),
            alarms=alarms,
            has_alarms=len(alarms) > 0,
            recipe=await client.get_ricetta_in_lavorazione(),
            total_pieces=int(await client.get_contapezzi_vita()),
            partial_pieces=int(await client.get_contapezzi_parziale()),
            batch_counter=int(await client.get_contatore_lotto()),
            lateral_bar_temp=await client.get_temperatura_barra_laterale(),
            frontal_bar_temp=await client.get_temperatura_barra_frontale(),
            triangle_position=await client.get_posizione_triangolo(),
            center_sealing_position=await client.get_posizione_center_sealing(),
        )
        
        await client.disconnect()
        return data
        
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore connessione OPC UA: {str(e)}")


# ============================================================================
# ENDPOINT MACCHINA (ESISTENTI)
# ============================================================================

@app.get("/")
async def root():
    """Endpoint radice con informazioni API"""
    return {
        "name": "MinipackTorre API with Database",
        "version": "2.0.0",
        "endpoints": {
            "/data": "GET - Tutti i dati della macchina",
            "/load-recipe": "POST - Carica una ricetta sulla macchina",
            "/reset-alarms": "POST - Reset allarmi macchina",
            "/health": "GET - Stato dell'API",
            "/clienti": "GET/POST - Gestione clienti",
            "/ricette": "GET/POST - Gestione ricette",
            "/commesse": "GET/POST - Gestione commesse",
            "/lavorazioni/start": "POST - Avvia lavorazione",
            "/lavorazioni/stop": "POST - Termina lavorazione",
            "/statistiche": "GET - Statistiche produzione e allarmi"
        }
    }


@app.get("/health")
async def health_check():
    """Health check dell'API"""
    status = await monitoring_service.get_current_status()
    return {
        "api_status": "ok",
        "monitoring_active": status['monitoring_active'],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/data", response_model=MachineData)
async def get_data():
    """Endpoint principale: restituisce tutti i dati della macchina"""
    return await get_machine_data()


@app.post("/load-recipe", response_model=LoadRecipeResponse)
async def load_recipe(request: LoadRecipeRequest):
    """Carica una ricetta sulla macchina"""
    client = MinipackTorreOPCUA(OPC_SERVER, OPC_USERNAME, OPC_PASSWORD)
    
    try:
        await client.connect()
        
        status_flags = await client.get_status_flags()
        if not status_flags['stop_automatico']:
            await client.disconnect()
            return LoadRecipeResponse(
                success=False,
                message="La macchina deve essere in stop automatico per caricare una ricetta",
                recipe_name=request.recipe_name
            )
        
        success = await client.carica_ricetta(request.recipe_name, timeout=30.0)
        await client.disconnect()
        
        if success:
            return LoadRecipeResponse(
                success=True,
                message=f"Ricetta '{request.recipe_name}' caricata con successo",
                recipe_name=request.recipe_name
            )
        else:
            return LoadRecipeResponse(
                success=False,
                message=f"Caricamento ricetta '{request.recipe_name}' fallito",
                recipe_name=request.recipe_name
            )
        
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore durante il caricamento: {str(e)}")


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
    
    # Verifica che il cliente esista
    cliente = await db.get_cliente(cliente_id)
    if not cliente:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    
    # Verifica che non ci siano commesse associate al cliente
    # Questo previene l'eliminazione di clienti con dati storici
    try:
        await db.delete_cliente(cliente_id)
        await db.disconnect()
        
        return {
            "success": True,
            "message": f"Cliente '{cliente.nome}' eliminato con successo",
            "id": cliente_id
        }
    except Exception as e:
        await db.disconnect()
        # Errore probabilmente dovuto a foreign key constraint
        raise HTTPException(
            status_code=400, 
            detail="Impossibile eliminare il cliente: potrebbe avere commesse associate"
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


@app.delete("/ricette/{ricetta_id}")
async def delete_ricetta(ricetta_id: int):
    """Elimina una ricetta"""
    db = DatabaseRepository()
    await db.connect()
    
    # Verifica che la ricetta esista
    ricetta = await db.get_ricetta(ricetta_id)
    if not ricetta:
        await db.disconnect()
        raise HTTPException(status_code=404, detail="Ricetta non trovata")
    
    # Verifica che non ci siano commesse associate alla ricetta
    # Questo previene l'eliminazione di ricette con dati storici
    try:
        await db.delete_ricetta(ricetta_id)
        await db.disconnect()
        
        return {
            "success": True,
            "message": f"Ricetta '{ricetta.nome}' eliminata con successo",
            "id": ricetta_id
        }
    except Exception as e:
        await db.disconnect()
        # Errore probabilmente dovuto a foreign key constraint
        raise HTTPException(
            status_code=400, 
            detail="Impossibile eliminare la ricetta: potrebbe essere utilizzata in commesse"
        )

# ============================================================================
# ENDPOINT COMMESSE
# ============================================================================

@app.get("/commesse", response_model=List[CommessaResponse])
async def get_commesse(attive_only: bool = False):
    """
    Recupera le commesse
    
    Query params:
        attive_only: Se true, recupera solo commesse non completate
    """
    db = DatabaseRepository()
    await db.connect()
    commesse = await db.get_commesse(attive_only=attive_only)
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
        created_at=c.created_at,
        updated_at=c.updated_at
    ) for c in commesse]


@app.post("/commesse", response_model=CommessaResponse)
async def create_commessa(commessa: CommessaCreate):
    """Crea una nuova commessa"""
    db = DatabaseRepository()
    await db.connect()
    
    new_commessa = Commessa(
        id=None,
        cliente_id=commessa.cliente_id,
        ricetta_id=commessa.ricetta_id,
        quantita_richiesta=commessa.quantita_richiesta,
        data_ordine=commessa.data_ordine,
        data_consegna_prevista=commessa.data_consegna_prevista
    )
    
    commessa_id = await db.create_commessa(new_commessa)
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
        created_at=created.created_at,
        updated_at=created.updated_at
    )


# ============================================================================
# ENDPOINT LAVORAZIONI
# ============================================================================

@app.post("/lavorazioni/start")
async def start_lavorazione(request: StartLavorazioneRequest):
    """Avvia una nuova lavorazione per una commessa"""
    try:
        await monitoring_service.start_lavorazione(request.commessa_id)
        return {
            "success": True,
            "message": f"Lavorazione avviata per commessa #{request.commessa_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/lavorazioni/stop")
async def stop_lavorazione():
    """Termina la lavorazione corrente"""
    try:
        await monitoring_service.stop_lavorazione()
        return {
            "success": True,
            "message": "Lavorazione terminata"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lavorazioni/current")
async def get_current_lavorazione():
    """Recupera informazioni sulla lavorazione corrente"""
    if not monitoring_service.current_lavorazione_id:
        return {
            "active": False,
            "lavorazione_id": None
        }
    
    db = DatabaseRepository()
    await db.connect()
    commessa = await db.get_commessa(monitoring_service.current_lavorazione_id)
    await db.disconnect()
    
    return {
        "active": True,
        "lavorazione_id": monitoring_service.current_lavorazione_id,
        "commessa": CommessaResponse(
            id=commessa.id,
            cliente_id=commessa.cliente_id,
            ricetta_id=commessa.ricetta_id,
            quantita_richiesta=commessa.quantita_richiesta,
            quantita_prodotta=commessa.quantita_prodotta,
            data_ordine=commessa.data_ordine,
            data_consegna_prevista=commessa.data_consegna_prevista,
            data_inizio_produzione=commessa.data_inizio_produzione,
            data_fine_produzione=commessa.data_fine_produzione,
            created_at=commessa.created_at,
            updated_at=commessa.updated_at
        )
    }


# ============================================================================
# ENDPOINT STATISTICHE
# ============================================================================

@app.get("/statistiche/overview")
async def get_statistiche_overview():
    """Recupera statistiche generali"""
    status = await monitoring_service.get_current_status()
    return status


@app.get("/statistiche/allarmi")
async def get_statistiche_allarmi(giorni: int = 7):
    """
    Recupera statistiche allarmi
    
    Query params:
        giorni: Numero di giorni da considerare (default: 7)
    """
    stats = await monitoring_service.get_alarm_statistics(days=giorni)
    
    # Arricchisci con messaggi
    for stat in stats:
        stat['messaggio'] = ALARM_MESSAGES.get(
            stat['codice_allarme'],
            f"Allarme sconosciuto"
        )
    
    return stats


@app.get("/statistiche/eventi")
async def get_statistiche_eventi(limit: int = 100):
    """
    Recupera eventi recenti
    
    Query params:
        limit: Numero massimo di eventi (default: 100)
    """
    events = await monitoring_service.get_recent_events(limit=limit)
    return events


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)