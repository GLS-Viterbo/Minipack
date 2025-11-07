"""
Client OPC UA per interfacciamento con macchina MinipackTorre
Controllo: SMART7 - Software: ELPLCCG0 (Pratika X1/X2)
"""

from asyncua import Client
from asyncua import ua
import asyncio
from typing import Optional, Dict, List
from enum import IntFlag, IntEnum


class StatusBits(IntFlag):
    """Bit della Status Word"""
    STOP_MANUALE = 1 << 0
    START_MANUALE = 1 << 1
    STOP_AUTOMATICO = 1 << 2
    START_AUTOMATICO = 1 << 3
    EMERGENZA = 1 << 4
    CARICAMENTO_RICETTA_OK = 1 << 5
    CARICAMENTO_RICETTA_KO = 1 << 6


class ControlBits(IntFlag):
    """Bit della Control Word"""
    RESET_ALLARMI = 1 << 0
    RICHIESTA_CARICAMENTO_RICETTA = 1 << 1


class MinipackTorreOPCUA:
    """
    Client OPC UA per macchina MinipackTorre con controllo SMART7
    """

    def __init__(self, server_url: str = "opc.tcp://10.58.156.65:4840", 
                username: str = "admin", 
                password: str = "Minipack1"):
        """
        Inizializza il client OPC UA
        
        Args:
            server_url: URL del server OPC UA (default: opc.tcp://10.58.156.65:4840)
            username: Username per autenticazione (default: admin)
            password: Password per autenticazione (default: Minipack1)
        """
        self.server_url = server_url
        self.username = username
        self.password = password
        self.client: Optional[Client] = None
        self.connected = False
        
        # Riferimenti ai nodi OPC UA (da inizializzare dopo la connessione)
        self.nodes = {}

    async def connect(self):
        """Connette al server OPC UA con autenticazione"""
        try:
            self.client = Client(url=self.server_url)
            
            # Configura autenticazione username/password
            self.client.set_user(self.username)
            self.client.set_password(self.password)
            
            await self.client.connect()
            self.connected = True
            print(f"Connesso al server OPC UA: {self.server_url}")
            print(f"Autenticato come: {self.username}")
                        
            # Inizializza i riferimenti ai nodi
            await self._init_nodes()
            
        except Exception as e:
            print(f"Errore durante la connessione: {e}")
            raise
    
    async def disconnect(self):
        """Disconnette dal server OPC UA"""
        if self.client and self.connected:
            await self.client.disconnect()
            self.connected = False
            print("Disconnesso dal server OPC UA")
    
    async def _init_nodes(self):
        """Inizializza i riferimenti ai nodi OPC UA"""
        
        # Nodi Diagnostica
        self.nodes['versione_software'] = ua.NodeId(50226, 0)
        self.nodes['nome_software'] = ua.NodeId(50227, 0)
        
        # Nodi Stato Macchina
        self.nodes['status_word'] = ua.NodeId(50229, 0)
        self.nodes['control_word'] = ua.NodeId(50230, 0)
        
        # Nodi Allarmi (9 oggetti)
        idx = 50234
        for i in range(9):
            self.nodes[f'allarme_{i}'] = ua.NodeId(idx, 0)
            idx += 1
        
        # Nodi I/O digitali
        self.nodes['input_1_16'] = ua.NodeId(50231, 0)
        self.nodes['input_17_32'] = ua.NodeId(50232, 0)
        self.nodes['output_1_16'] = ua.NodeId(50233, 0)
        self.nodes['output_17_32'] = ua.NodeId(50243, 0)
        
        # Nodi Processo
        self.nodes['posizione_triangolo'] = ua.NodeId(50245, 0)
        self.nodes['posizione_center_sealing'] = ua.NodeId(50246, 0)
        self.nodes['temp_barra_laterale'] = ua.NodeId(50247, 0)
        self.nodes['temp_barra_frontale'] = ua.NodeId(50248, 0)
        self.nodes['contapezzi_vita'] = ua.NodeId(50249, 0)
        self.nodes['contapezzi_parziale'] = ua.NodeId(50250, 0)
        self.nodes['contatore_lotto'] = ua.NodeId(50251, 0)
        self.nodes['ricetta_in_lavorazione'] = ua.NodeId(50252, 0)
        self.nodes['ricetta_da_caricare'] = ua.NodeId(50253, 0)
    
    async def _get_node(self, node_key: str):
        """Ottiene il nodo OPC UA dal suo identificatore"""
        if node_key not in self.nodes:
            raise ValueError(f"Nodo {node_key} non trovato")
        return self.client.get_node(self.nodes[node_key])
    
    async def _get_node_datatype(self, node_key: str):
        """Ottiene il tipo di dato di un nodo OPC UA"""
        node = await self._get_node(node_key)
        data_type = await node.read_data_type()
        return data_type
    
    # === DIAGNOSTICA ===
    
    async def get_versione_software(self) -> str:
        """Legge la versione del software"""
        node = await self._get_node('versione_software')
        return await node.read_value()
    
    async def get_nome_software(self) -> str:
        """Legge il nome del software"""
        node = await self._get_node('nome_software')
        return await node.read_value()
    
    # === STATO MACCHINA ===
    
    async def get_status_word(self) -> int:
        """Legge la status word"""
        node = await self._get_node('status_word')
        return await node.read_value()
    
    async def get_status_flags(self) -> Dict[str, bool]:
        """Legge e decodifica la status word"""
        status = await self.get_status_word()
        return {
            'stop_manuale': bool(status & StatusBits.STOP_MANUALE),
            'start_manuale': bool(status & StatusBits.START_MANUALE),
            'stop_automatico': bool(status & StatusBits.STOP_AUTOMATICO),
            'start_automatico': bool(status & StatusBits.START_AUTOMATICO),
            'emergenza': bool(status & StatusBits.EMERGENZA),
            'caricamento_ricetta_ok': bool(status & StatusBits.CARICAMENTO_RICETTA_OK),
            'caricamento_ricetta_ko': bool(status & StatusBits.CARICAMENTO_RICETTA_KO),
        }
    
    async def get_control_word(self) -> int:
        """Legge la control word"""
        node = await self._get_node('control_word')
        return await node.read_value()
    
    async def set_control_word(self, value: int):
        """Scrive la control word"""
        node = await self._get_node('control_word')
        
        
        # Prova con Variant UInt16
        try:
            dv = ua.DataValue(ua.Variant(value, ua.VariantType.UInt16))
            await node.write_value(dv)
            return
        except Exception as e:
            print(f"Scrittura con Variant UInt16 fallita: {e}")
            raise Exception(f"Impossibile scrivere la control word. Tutti i metodi hanno fallito.")
    
    async def reset_allarmi(self):
        """Attiva il reset degli allarmi"""
        control = await self.get_control_word()
        control |= ControlBits.RESET_ALLARMI
        await self.set_control_word(control)
        # Resetta il bit dopo un breve delay
        await asyncio.sleep(0.5)
        control &= ~ControlBits.RESET_ALLARMI
        await self.set_control_word(control)
    
    async def get_allarmi_attivi(self) -> List[int]:
        """Legge tutti gli allarmi attivi"""
        allarmi = []
        for i in range(9):
            node = await self._get_node(f'allarme_{i}')
            codice = await node.read_value()
            if codice != 0:
                allarmi.append(codice)
        return allarmi
    
    # === PROCESSO ===
    
    async def get_posizione_triangolo(self) -> float:
        """Legge la posizione del triangolo in mm"""
        node = await self._get_node('posizione_triangolo')
        return await node.read_value()
    
    async def get_posizione_center_sealing(self) -> float:
        """Legge la posizione del center sealing in mm"""
        node = await self._get_node('posizione_center_sealing')
        return await node.read_value()
    
    async def get_temperatura_barra_laterale(self) -> float:
        """Legge la temperatura della barra laterale in °C"""
        node = await self._get_node('temp_barra_laterale')
        return await node.read_value()
    
    async def get_temperatura_barra_frontale(self) -> float:
        """Legge la temperatura della barra frontale in °C"""
        node = await self._get_node('temp_barra_frontale')
        return await node.read_value()
    
    async def get_contapezzi_vita(self) -> float:
        """Legge il contatore totale dei pezzi"""
        node = await self._get_node('contapezzi_vita')
        return await node.read_value()
    
    async def get_contapezzi_parziale(self) -> float:
        """Legge il contatore parziale dei pezzi"""
        node = await self._get_node('contapezzi_parziale')
        return await node.read_value()
    
    async def get_contatore_lotto(self) -> float:
        """Legge il contatore del lotto corrente"""
        node = await self._get_node('contatore_lotto')
        return await node.read_value()
    
    async def set_contatore_lotto(self, valore: float):
        """Imposta il contatore del lotto"""
        node = await self._get_node('contatore_lotto')
        
        
        # Prova con Variant Double
        try:
            dv = ua.DataValue(ua.Variant(valore, ua.VariantType.Double))
            await node.write_value(dv)
            return
        except Exception as e:
            print(f"Scrittura con Variant Double fallita: {e}")
            raise Exception(f"Impossibile scrivere il contatore lotto. Tutti i metodi hanno fallito.")
    
    async def get_ricetta_in_lavorazione(self) -> str:
        """Legge il nome della ricetta in lavorazione"""
        node = await self._get_node('ricetta_in_lavorazione')
        return await node.read_value()
    
    async def get_ricetta_da_caricare(self) -> str:
        """Legge il nome della ricetta da caricare"""
        node = await self._get_node('ricetta_da_caricare')
        return await node.read_value()
    
    async def set_ricetta_da_caricare(self, nome_ricetta: str):
        """Imposta il nome della ricetta da caricare"""
        node = await self._get_node('ricetta_da_caricare')
        
        
        # Prova con Variant String
        try:
            dv = ua.DataValue(ua.Variant(nome_ricetta, ua.VariantType.String))
            await node.write_value(dv)
            return
        except Exception as e:
            print(f"Scrittura con Variant String fallita: {e}")
    
    # === CARICAMENTO RICETTE ===
    
    async def carica_ricetta(self, nome_ricetta: str, timeout: float = 120.0) -> bool:
        """
        Carica una ricetta seguendo la procedura OPC UA
        
        Args:
            nome_ricetta: Nome della ricetta da caricare
            timeout: Timeout in secondi per l'operazione
            
        Returns:
            True se il caricamento è riuscito, False altrimenti
        """
        try:
            # 1. Verifica che la macchina sia in stop automatico
            status = await self.get_status_flags()
            if not status['stop_automatico']:
                print("ERRORE: La macchina deve essere in stop automatico")
                return False
            
            # 2. Imposta la ricetta da caricare
            await self.set_ricetta_da_caricare(nome_ricetta)
            print(f"Ricetta impostata: {nome_ricetta}")
            
            # 3. Attiva il bit di richiesta caricamento
            control = await self.get_control_word()
            control |= ControlBits.RICHIESTA_CARICAMENTO_RICETTA
            await self.set_control_word(control)
            print("Richiesta caricamento ricetta inviata")
            
            # 4. Attendi conferma (OK o KO)
            start_time = asyncio.get_event_loop().time()
            while True:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print("TIMEOUT: Il caricamento della ricetta ha superato il timeout")
                    # Reset del bit di richiesta
                    control &= ~ControlBits.RICHIESTA_CARICAMENTO_RICETTA
                    await self.set_control_word(control)
                    return False
                
                status = await self.get_status_flags()
                
                if status['caricamento_ricetta_ok']:
                    print("Caricamento ricetta completato con successo")
                    # Reset del bit di richiesta
                    control &= ~ControlBits.RICHIESTA_CARICAMENTO_RICETTA
                    await self.set_control_word(control)
                    return True
                
                if status['caricamento_ricetta_ko']:
                    print("ERRORE: Caricamento ricetta fallito")
                    # Reset del bit di richiesta
                    control &= ~ControlBits.RICHIESTA_CARICAMENTO_RICETTA
                    await self.set_control_word(control)
                    return False
                
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"Errore durante il caricamento della ricetta: {e}")
            return False