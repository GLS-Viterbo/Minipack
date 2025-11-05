"""
REST API per monitoraggio macchina MinipackTorre
Endpoint singolo che restituisce tutti i dati in una chiamata
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio
from minipack import MinipackTorreOPCUA

# Configurazione server OPC UA
OPC_SERVER = "opc.tcp://10.58.156.65:4840"
OPC_USERNAME = "admin"
OPC_PASSWORD = "Minipack1"

app = FastAPI(
    title="MinipackTorre API",
    description="API per monitoraggio real-time macchina confezionatrice",
    version="1.0.0"
)

# Abilita CORS per permettere chiamate da browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    # Sistema
    software_name: str
    software_version: str
    
    # Stato
    status: MachineStatus
    
    # Allarmi
    alarms: List[AlarmInfo]
    has_alarms: bool
    
    # Produzione
    recipe: str
    total_pieces: int
    partial_pieces: int
    batch_counter: int
    
    # Temperature
    lateral_bar_temp: float
    frontal_bar_temp: float
    
    # Posizioni
    triangle_position: float
    center_sealing_position: float


class LoadRecipeRequest(BaseModel):
    recipe_name: str


class LoadRecipeResponse(BaseModel):
    success: bool
    message: str
    recipe_name: str


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
            
            # Sistema
            software_name=await client.get_nome_software(),
            software_version=await client.get_versione_software(),
            
            # Stato
            status=MachineStatus(
                stop_manuale=status_flags['stop_manuale'],
                start_manuale=status_flags['start_manuale'],
                stop_automatico=status_flags['stop_automatico'],
                start_automatico=status_flags['start_automatico'],
                emergenza=status_flags['emergenza'],
                status_text=get_status_text(status_flags)
            ),
            
            # Allarmi
            alarms=alarms,
            has_alarms=len(alarms) > 0,
            
            # Produzione
            recipe=await client.get_ricetta_in_lavorazione(),
            total_pieces=int(await client.get_contapezzi_vita()),
            partial_pieces=int(await client.get_contapezzi_parziale()),
            batch_counter=int(await client.get_contatore_lotto()),
            
            # Temperature
            lateral_bar_temp=await client.get_temperatura_barra_laterale(),
            frontal_bar_temp=await client.get_temperatura_barra_frontale(),
            
            # Posizioni
            triangle_position=await client.get_posizione_triangolo(),
            center_sealing_position=await client.get_posizione_center_sealing(),
        )
        
        await client.disconnect()
        return data
        
    except Exception as e:
        await client.disconnect()
        raise HTTPException(status_code=500, detail=f"Errore connessione OPC UA: {str(e)}")


@app.get("/")
async def root():
    """Endpoint radice con informazioni API"""
    return {
        "name": "MinipackTorre API",
        "version": "1.0.0",
        "endpoints": {
            "/data": "GET - Tutti i dati della macchina",
            "/load-recipe": "POST - Carica una ricetta sulla macchina",
            "/reset-alarms": "POST - Reset allarmi macchina",
            "/health": "GET - Stato dell'API"
        }
    }


@app.get("/health")
async def health_check():
    """Health check dell'API"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/data", response_model=MachineData)
async def get_data():
    """
    Endpoint principale: restituisce tutti i dati della macchina in una singola chiamata
    
    Returns:
        MachineData: Oggetto con tutti i dati della macchina
    """
    return await get_machine_data()


@app.post("/load-recipe", response_model=LoadRecipeResponse)
async def load_recipe(request: LoadRecipeRequest):
    """
    Carica una ricetta sulla macchina
    
    Args:
        request: Oggetto contenente il nome della ricetta da caricare
        
    Returns:
        LoadRecipeResponse: Oggetto con l'esito dell'operazione
        
    Example:
        POST /load-recipe
        {
            "recipe_name": "RICETTA_001"
        }
    """
    client = MinipackTorreOPCUA(OPC_SERVER, OPC_USERNAME, OPC_PASSWORD)
    
    try:
        await client.connect()
        
        # Verifica che la macchina sia in stop automatico
        status_flags = await client.get_status_flags()
        if not status_flags['stop_automatico']:
            await client.disconnect()
            return LoadRecipeResponse(
                success=False,
                message="La macchina deve essere in stop automatico per caricare una ricetta",
                recipe_name=request.recipe_name
            )
        
        # Esegue il caricamento della ricetta
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
    """
    Esegue il reset degli allarmi sulla macchina
    
    Returns:
        dict: Esito dell'operazione
    """
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)