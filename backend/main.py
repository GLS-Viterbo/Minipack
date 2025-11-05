"""
Dashboard Web per Monitoraggio Macchina MinipackTorre
Interfaccia professionale con Gooey per visualizzazione metriche real-time
"""

from gooey import Gooey, GooeyParser
import asyncio
from datetime import datetime
from minipack import MinipackTorreOPCUA, AlarmCode
import sys


# Dizionario per mappare i codici allarme ai messaggi
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


def format_stato_macchina(status_flags):
    """Formatta lo stato della macchina in modo leggibile"""
    if status_flags['emergenza']:
        return "🔴 EMERGENZA"
    elif status_flags['start_automatico']:
        return "🟢 IN PRODUZIONE (AUTO)"
    elif status_flags['start_manuale']:
        return "🟡 IN MARCIA (MANUALE)"
    elif status_flags['stop_automatico']:
        return "🟠 PRONTA (STOP AUTO)"
    elif status_flags['stop_manuale']:
        return "⚪ FERMATA (STOP MANUALE)"
    else:
        return "⚫ STATO SCONOSCIUTO"


def format_allarmi(allarmi_codici):
    """Formatta gli allarmi attivi"""
    if not allarmi_codici:
        return "✅ Nessun allarme attivo"
    
    result = "⚠️  ALLARMI ATTIVI:\n"
    for codice in allarmi_codici:
        messaggio = ALARM_MESSAGES.get(codice, f"Allarme sconosciuto (codice {codice})")
        result += f"   • A{codice:03d} - {messaggio}\n"
    return result.strip()


async def get_machine_data(server_url, username="admin", password="Minipack1"):
    """Recupera i dati dalla macchina"""
    client = MinipackTorreOPCUA(server_url, username, password)
    
    try:
        await client.connect()
        
        # Recupera tutti i dati
        status = await client.get_status_flags()
        allarmi = await client.get_allarmi_attivi()
        
        data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'versione_sw': await client.get_versione_software(),
            'nome_sw': await client.get_nome_software(),
            'stato_macchina': format_stato_macchina(status),
            'allarmi': format_allarmi(allarmi),
            'ricetta': await client.get_ricetta_in_lavorazione(),
            'temp_laterale': await client.get_temperatura_barra_laterale(),
            'temp_frontale': await client.get_temperatura_barra_frontale(),
            'contapezzi_vita': int(await client.get_contapezzi_vita()),
            'contapezzi_parziale': int(await client.get_contapezzi_parziale()),
            'contatore_lotto': int(await client.get_contatore_lotto()),
            'pos_triangolo': await client.get_posizione_triangolo(),
            'pos_center_sealing': await client.get_posizione_center_sealing(),
        }
        
        await client.disconnect()
        return data
        
    except Exception as e:
        if client:
            await client.disconnect()
        raise Exception(f"Errore di connessione: {str(e)}")


def display_dashboard(data):
    """Visualizza la dashboard con i dati"""
    print("\n" + "="*80)
    print(" "*20 + "DASHBOARD MINIPACKTORRE - INDUSTRIA 4.0")
    print("="*80)
    
    print(f"\n⏰ Ultimo aggiornamento: {data['timestamp']}")
    
    print("\n" + "─"*80)
    print("📊 INFORMAZIONI SISTEMA")
    print("─"*80)
    print(f"Software: {data['nome_sw']}")
    print(f"Versione: {data['versione_sw']}")
    
    print("\n" + "─"*80)
    print("🏭 STATO MACCHINA")
    print("─"*80)
    print(f"Stato: {data['stato_macchina']}")
    print(f"\n{data['allarmi']}")
    
    print("\n" + "─"*80)
    print("📦 PRODUZIONE")
    print("─"*80)
    print(f"Ricetta in lavorazione: {data['ricetta']}")
    print(f"Pezzi totali (vita):    {data['contapezzi_vita']:,}")
    print(f"Pezzi parziali:         {data['contapezzi_parziale']:,}")
    print(f"Contatore lotto:        {data['contatore_lotto']:,}")
    
    print("\n" + "─"*80)
    print("🌡️  TEMPERATURE")
    print("─"*80)
    print(f"Barra laterale:  {data['temp_laterale']:.1f}°C")
    print(f"Barra frontale:  {data['temp_frontale']:.1f}°C")
    
    print("\n" + "─"*80)
    print("📍 POSIZIONI")
    print("─"*80)
    print(f"Triangolo:       {data['pos_triangolo']:.2f} mm")
    print(f"Center Sealing:  {data['pos_center_sealing']:.2f} mm")
    
    print("\n" + "="*80 + "\n")


@Gooey(
    program_name="Dashboard MinipackTorre",
    program_description="Monitoraggio Real-Time Macchina Industria 4.0",
    default_size=(800, 700),
    navigation='SIDEBAR',
    sidebar_title="Menu",
    header_bg_color='#1e3a5f',
    body_bg_color='#f5f5f5',
    footer_bg_color='#1e3a5f',
    terminal_font_family='Courier New',
    terminal_font_size=10,
    show_success_modal=False,
    show_failure_modal=True,
    richtext_controls=False,
    menu=[{
        'name': 'Info',
        'items': [{
            'type': 'AboutDialog',
            'menuTitle': 'Informazioni',
            'name': 'Dashboard MinipackTorre',
            'description': 'Sistema di monitoraggio per macchine confezionatrici\nIndustria 4.0 - OPC UA Interface',
            'version': '1.0.0',
            'copyright': '2022-2024',
            'website': 'www.elcoelettronica.it',
            'developer': 'Elco Elettronica Automation Srl'
        }]
    }]
)
def main():
    parser = GooeyParser(description="Dashboard di monitoraggio per macchina MinipackTorre")
    
    # Sezione Connessione
    connection_group = parser.add_argument_group(
        "Connessione",
        "Configurazione connessione al server OPC UA"
    )
    
    connection_group.add_argument(
        '--server',
        metavar='Server OPC UA',
        default='opc.tcp://10.58.156.65:4840',
        help='Indirizzo del server OPC UA',
        widget='TextField',
        gooey_options={
            'placeholder': 'opc.tcp://10.58.156.65:4840'
        }
    )
    
    connection_group.add_argument(
        '--username',
        metavar='Username',
        default='admin',
        help='Username per autenticazione OPC UA',
        widget='TextField'
    )
    
    connection_group.add_argument(
        '--password',
        metavar='Password',
        default='Minipack1',
        help='Password per autenticazione OPC UA',
        widget='PasswordField'
    )
    
    # Sezione Azioni
    actions_group = parser.add_argument_group(
        "Azioni",
        "Operazioni disponibili"
    )
    
    actions_group.add_argument(
        '--action',
        metavar='Azione',
        choices=['Visualizza Dashboard', 'Reset Allarmi', 'Carica Ricetta'],
        default='Visualizza Dashboard',
        help='Seleziona l\'azione da eseguire',
        widget='Dropdown'
    )
    
    actions_group.add_argument(
        '--ricetta',
        metavar='Nome Ricetta',
        default='',
        help='Nome della ricetta da caricare (solo per azione "Carica Ricetta")',
        widget='TextField',
        gooey_options={
            'placeholder': 'Es: RICETTA_001'
        }
    )
    
    # Sezione Opzioni Avanzate
    advanced_group = parser.add_argument_group(
        "Opzioni Avanzate",
        "Configurazioni aggiuntive"
    )
    
    advanced_group.add_argument(
        '--refresh',
        metavar='Intervallo Aggiornamento (sec)',
        type=int,
        default=5,
        help='Intervallo di aggiornamento dati in secondi',
        widget='IntegerField',
        gooey_options={
            'min': 1,
            'max': 60
        }
    )
    
    advanced_group.add_argument(
        '--continuous',
        metavar='Monitoraggio Continuo',
        action='store_true',
        help='Abilita il monitoraggio continuo (aggiornamento automatico)',
        widget='CheckBox'
    )
    
    args = parser.parse_args()
    
    print("\n🔌 Connessione al server OPC UA...")
    print(f"   Server: {args.server}\n")
    
    try:
        if args.action == 'Visualizza Dashboard':
            if args.continuous:
                print("🔄 Modalità monitoraggio continuo attivata")
                print(f"   Aggiornamento ogni {args.refresh} secondi")
                print("   Premi Ctrl+C per interrompere\n")
                
                loop_count = 0
                while True:
                    try:
                        data = asyncio.run(get_machine_data(args.server, args.username, args.password))
                        display_dashboard(data)
                        
                        loop_count += 1
                        print(f"⏳ Prossimo aggiornamento tra {args.refresh} secondi... (ciclo #{loop_count})")
                        asyncio.run(asyncio.sleep(args.refresh))
                        
                    except KeyboardInterrupt:
                        print("\n\n⛔ Monitoraggio interrotto dall'utente")
                        break
            else:
                data = asyncio.run(get_machine_data(args.server, args.username, args.password))
                display_dashboard(data)
                print("✅ Dati recuperati con successo!")
        
        elif args.action == 'Reset Allarmi':
            async def reset_allarmi():
                client = MinipackTorreOPCUA(args.server, args.username, args.password)
                await client.connect()
                await client.reset_allarmi()
                await client.disconnect()
            
            print("🔧 Esecuzione reset allarmi...")
            asyncio.run(reset_allarmi())
            print("✅ Reset allarmi completato!")
        
        elif args.action == 'Carica Ricetta':
            if not args.ricetta:
                print("❌ ERRORE: Specificare il nome della ricetta da caricare!")
                sys.exit(1)
            
            async def carica_ricetta():
                client = MinipackTorreOPCUA(args.server, args.username, args.password)
                await client.connect()
                success = await client.carica_ricetta(args.ricetta)
                await client.disconnect()
                return success
            
            print(f"📋 Caricamento ricetta: {args.ricetta}")
            success = asyncio.run(carica_ricetta())
            
            if success:
                print("✅ Ricetta caricata con successo!")
            else:
                print("❌ ERRORE: Caricamento ricetta fallito!")
                sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ ERRORE: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()