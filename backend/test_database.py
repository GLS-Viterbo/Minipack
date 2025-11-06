"""
Script di esempio per testare il sistema di database e monitoraggio
Dimostra l'utilizzo completo delle funzionalità
"""

import asyncio
from datetime import datetime, date, timedelta
from database import DatabaseRepository, Cliente, Ricetta, Commessa
from monitoring_service import MonitoringService


async def test_database_operations():
    """Test operazioni CRUD sul database"""
    print("="*80)
    print("TEST OPERAZIONI DATABASE")
    print("="*80)
    
    db = DatabaseRepository("test_minipack.db")
    await db.connect()
    
    # ========================================================================
    # 1. CLIENTI
    # ========================================================================
    print("\n--- CREAZIONE CLIENTI ---")
    
    cliente1 = Cliente(
        id=None,
        nome="ACME Corporation",
        partita_iva="12345678901",
        codice_fiscale=None
    )
    id1 = await db.create_cliente(cliente1)
    print(f"✅ Cliente creato con ID: {id1}")
    
    cliente2 = Cliente(
        id=None,
        nome="Beta Industries SRL",
        partita_iva="98765432109"
    )
    id2 = await db.create_cliente(cliente2)
    print(f"✅ Cliente creato con ID: {id2}")
    
    # Lista clienti
    print("\n--- LISTA CLIENTI ---")
    clienti = await db.get_clienti()
    for c in clienti:
        print(f"  • #{c.id} - {c.nome} (P.IVA: {c.partita_iva})")
    
    # ========================================================================
    # 2. RICETTE
    # ========================================================================
    print("\n--- CREAZIONE RICETTE ---")
    
    ricetta1 = Ricetta(
        id=None,
        nome="RICETTA_STANDARD",
        descrizione="Configurazione standard per confezionamento"
    )
    rid1 = await db.create_ricetta(ricetta1)
    print(f"✅ Ricetta creata con ID: {rid1}")
    
    ricetta2 = Ricetta(
        id=None,
        nome="RICETTA_ALTA_VELOCITA",
        descrizione="Configurazione ottimizzata per alta produttività"
    )
    rid2 = await db.create_ricetta(ricetta2)
    print(f"✅ Ricetta creata con ID: {rid2}")
    
    # Lista ricette
    print("\n--- LISTA RICETTE ---")
    ricette = await db.get_ricette()
    for r in ricette:
        print(f"  • #{r.id} - {r.nome}")
        print(f"    {r.descrizione}")
    
    # ========================================================================
    # 3. COMMESSE
    # ========================================================================
    print("\n--- CREAZIONE COMMESSE ---")
    
    oggi = date.today()
    
    commessa1 = Commessa(
        id=None,
        cliente_id=id1,
        ricetta_id=rid1,
        quantita_richiesta=1000,
        data_ordine=oggi.isoformat(),
        data_consegna_prevista=(oggi + timedelta(days=7)).isoformat()
    )
    cid1 = await db.create_commessa(commessa1)
    print(f"✅ Commessa creata con ID: {cid1}")
    
    commessa2 = Commessa(
        id=None,
        cliente_id=id2,
        ricetta_id=rid2,
        quantita_richiesta=2500,
        data_ordine=oggi.isoformat(),
        data_consegna_prevista=(oggi + timedelta(days=14)).isoformat()
    )
    cid2 = await db.create_commessa(commessa2)
    print(f"✅ Commessa creata con ID: {cid2}")
    
    # Lista commesse
    print("\n--- LISTA COMMESSE ---")
    commesse = await db.get_commesse()
    for c in commesse:
        print(f"  • Commessa #{c.id}")
        print(f"    Cliente ID: {c.cliente_id}")
        print(f"    Ricetta ID: {c.ricetta_id}")
        print(f"    Quantità: {c.quantita_prodotta}/{c.quantita_richiesta}")
        print(f"    Consegna prevista: {c.data_consegna_prevista}")
    
    # ========================================================================
    # 4. EVENTI MACCHINA
    # ========================================================================
    print("\n--- REGISTRAZIONE EVENTI ---")
    
    # Simula alcuni eventi
    await db.insert_evento_macchina(
        tipo_evento="CAMBIO_STATO",
        stato_macchina="START_AUTOMATICO",
        lavorazione_id=cid1,
        dati={
            'note': 'Avvio produzione commessa #1'
        }
    )
    print("✅ Evento registrato: CAMBIO_STATO")
    
    await db.insert_evento_macchina(
        tipo_evento="CAMBIO_RICETTA",
        stato_macchina="START_AUTOMATICO",
        lavorazione_id=cid1,
        dati={
            'ricetta_precedente': 'NESSUNA',
            'ricetta_nuova': 'RICETTA_STANDARD'
        }
    )
    print("✅ Evento registrato: CAMBIO_RICETTA")
    
    # Lista eventi recenti
    print("\n--- EVENTI RECENTI ---")
    eventi = await db.get_eventi_macchina(limit=10)
    for e in eventi:
        print(f"  • {e.timestamp} - {e.tipo_evento}")
        print(f"    Stato: {e.stato_macchina}")
    
    # ========================================================================
    # 5. ALLARMI
    # ========================================================================
    print("\n--- GESTIONE ALLARMI ---")
    
    # Simula attivazione allarme
    print("Simulazione allarme attivo...")
    allarme_id = await db.insert_allarme(
        codice_allarme=10,  # MACCHINA IN RISCALDAMENTO
        lavorazione_id=cid1
    )
    print(f"✅ Allarme attivato con ID: {allarme_id}")
    
    # Attendi un po'
    await asyncio.sleep(2)
    
    # Risolvi allarme
    print("Risoluzione allarme...")
    await db.chiudi_allarme(codice_allarme=10)
    print("✅ Allarme risolto")
    
    # Statistiche allarmi
    print("\n--- STATISTICHE ALLARMI (ultimi 30 giorni) ---")
    stats = await db.get_statistiche_allarmi(giorni=30)
    for stat in stats:
        print(f"  • Allarme {stat['codice_allarme']}")
        print(f"    Occorrenze: {stat['conteggio']}")
        if stat['durata_media_secondi']:
            print(f"    Durata media: {stat['durata_media_secondi']:.1f} secondi")
    
    # ========================================================================
    # 6. STATISTICHE DATABASE
    # ========================================================================
    print("\n--- STATISTICHE DATABASE ---")
    db_stats = await db.get_database_stats()
    for key, value in db_stats.items():
        print(f"  • {key}: {value}")
    
    await db.disconnect()
    print("\n✅ Test completato con successo!\n")


async def test_monitoring_service():
    """Test servizio di monitoraggio (richiede connessione alla macchina)"""
    print("="*80)
    print("TEST SERVIZIO DI MONITORAGGIO")
    print("="*80)
    print("\nNOTA: Questo test richiede connessione al server OPC UA")
    print("Se la macchina non è disponibile, il test fallirà\n")
    
    # Configurazione
    OPC_SERVER = "opc.tcp://10.58.156.65:4840"
    OPC_USERNAME = "admin"
    OPC_PASSWORD = "Minipack1"
    
    # Crea servizio
    service = MonitoringService(
        opc_server=OPC_SERVER,
        opc_username=OPC_USERNAME,
        opc_password=OPC_PASSWORD,
        polling_interval=5,
        db_path="test_minipack.db"
    )
    
    try:
        # Avvia monitoraggio
        print("🚀 Avvio servizio di monitoraggio...")
        await service.start()
        
        # Verifica che sia una commessa disponibile
        db = DatabaseRepository("test_minipack.db")
        await db.connect()
        commesse = await db.get_commesse(attive_only=True)
        await db.disconnect()
        
        if not commesse:
            print("⚠️  Nessuna commessa disponibile - creo una commessa di test")
            # Qui dovresti creare una commessa di test se necessario
        else:
            commessa_id = commesse[0].id
            
            # Avvia lavorazione
            print(f"\n--- AVVIO LAVORAZIONE per commessa #{commessa_id} ---")
            await service.start_lavorazione(commessa_id)
            
            # Monitora per 30 secondi
            print("\n--- MONITORAGGIO IN CORSO (30 secondi) ---")
            for i in range(6):
                await asyncio.sleep(5)
                status = await service.get_current_status()
                print(f"  • Ciclo {i+1}/6 - Lavorazione attiva: {status['current_lavorazione_id']}")
            
            # Mostra eventi
            print("\n--- EVENTI REGISTRATI ---")
            events = await service.get_recent_events(limit=10)
            for event in events[:5]:  # Mostra solo i primi 5
                print(f"  • {event.timestamp}")
                print(f"    Tipo: {event.tipo_evento}")
                print(f"    Stato: {event.stato_macchina}")
            
            # Termina lavorazione
            print("\n--- FINE LAVORAZIONE ---")
            await service.stop_lavorazione()
        
        print("\n✅ Test monitoraggio completato!")
        
    except Exception as e:
        print(f"\n❌ Errore durante il test: {e}")
        print("Probabilmente la macchina non è raggiungibile")
    
    finally:
        await service.stop()


async def main():
    """Esegue tutti i test"""
    print("\n" + "="*80)
    print("SUITE DI TEST - MINIPACKTORRE DATABASE & MONITORING")
    print("="*80 + "\n")
    
    # Test 1: Operazioni database
    await test_database_operations()
    
    # Test 2: Servizio monitoraggio (opzionale)
    risposta = input("\nVuoi testare il servizio di monitoraggio? (richiede connessione macchina) [s/n]: ")
    if risposta.lower() == 's':
        await test_monitoring_service()
    else:
        print("Test monitoraggio saltato")
    
    print("\n" + "="*80)
    print("TUTTI I TEST COMPLETATI")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())