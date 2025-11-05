# MinipackTorre Dashboard - React Interface

Dashboard web professionale per il monitoraggio real-time della macchina confezionatrice MinipackTorre con controllo SMART7.

## 🚀 Caratteristiche

- **Monitoraggio Real-Time**: Visualizzazione dello stato macchina con aggiornamento automatico
- **Design Professionale**: Interfaccia moderna e responsive
- **Componenti Modulari**: Architettura estensibile per future funzionalità
- **Gestione Allarmi**: Visualizzazione chiara degli allarmi attivi con codici e descrizioni
- **Dati di Produzione**: Monitoraggio contapezzi, ricette e lotti
- **Temperature**: Visualizzazione temperature delle barre saldanti con indicatori visivi
- **Posizioni**: Tracciamento posizioni triangolo e center sealing

## 📋 Prerequisiti

- Node.js 16+ e npm
- Backend FastAPI in esecuzione (app.py)
- Connessione alla macchina MinipackTorre via OPC UA

## 🛠️ Installazione

1. **Installa le dipendenze:**
```bash
cd minipack-dashboard
npm install
```

2. **Configura il backend:**
Assicurati che il server FastAPI sia in esecuzione sulla porta 8000:
```bash
# Nella directory principale del progetto
python app.py
```

3. **Avvia l'applicazione React:**
```bash
npm run dev
```

L'applicazione sarà disponibile su `http://localhost:3000`

## 📁 Struttura del Progetto

```
minipack-dashboard/
├── src/
│   ├── components/
│   │   ├── Header/           # Header con controlli
│   │   ├── StatusCard/       # Stato macchina e allarmi
│   │   ├── SystemInfo/       # Informazioni sistema
│   │   ├── ProductionData/   # Dati produzione
│   │   ├── TemperatureData/  # Visualizzazione temperature
│   │   ├── PositionData/     # Posizioni meccaniche
│   │   └── LoadingError/     # Stati loading/errore
│   ├── hooks/
│   │   └── useMachineData.js # Hook per polling dati
│   ├── services/
│   │   └── api.js            # Servizio API
│   ├── App.jsx               # Componente principale
│   ├── App.css               # Stili applicazione
│   ├── main.jsx              # Entry point
│   └── index.css             # Stili globali
├── package.json
├── vite.config.js
└── index.html
```

## 🔧 Configurazione

### Intervallo di Aggiornamento

L'intervallo di polling predefinito è 5 secondi. Per modificarlo, edita `src/App.jsx`:

```javascript
const { data, loading, error, refresh, isPolling, togglePolling } = useMachineData(5000); // millisecondi
```

### URL del Backend

Il proxy è configurato in `vite.config.js` per reindirizzare le chiamate `/api` al backend:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

## 🎨 Personalizzazione

### Colori e Temi

I colori sono definiti in `src/index.css` usando variabili CSS:

```css
:root {
  --primary: #1e3a5f;
  --secondary: #4a90e2;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  /* ... */
}
```

### Componenti

Tutti i componenti sono modulari e facilmente personalizzabili:

- **Header**: Titolo, pulsanti e timestamp
- **StatusCard**: Stato macchina e lista allarmi
- **ProductionData**: Dati di produzione
- **TemperatureData**: Temperature con barre colorate
- **PositionData**: Posizioni meccaniche

## 🔮 Estensioni Future

La dashboard è già predisposta per future funzionalità:

### 1. Caricamento Ricette

Il service API include già un metodo placeholder:

```javascript
// src/services/api.js
static async loadRecipe(recipeName) {
  // TODO: Implementare quando il backend supporterà questa funzionalità
}
```

Implementazione suggerita:

```javascript
// Nuovo componente RecipeLoader
export function RecipeLoader({ currentRecipe, onLoadRecipe }) {
  const [recipeName, setRecipeName] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLoad = async () => {
    setLoading(true);
    try {
      await ApiService.loadRecipe(recipeName);
      // Mostra successo
    } catch (error) {
      // Gestisci errore
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Carica Ricetta</h3>
      <input 
        value={recipeName} 
        onChange={(e) => setRecipeName(e.target.value)}
        placeholder="Nome ricetta..."
      />
      <button onClick={handleLoad} disabled={loading}>
        {loading ? 'Caricamento...' : 'Carica'}
      </button>
    </div>
  );
}
```

### 2. Grafici Storici

Integrazione con librerie di charting (es. Recharts):

```javascript
import { LineChart, Line, XAxis, YAxis } from 'recharts';

export function TemperatureChart({ data }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="timestamp" />
      <YAxis />
      <Line type="monotone" dataKey="temperature" stroke="#4a90e2" />
    </LineChart>
  );
}
```

### 3. Notifiche Real-Time

WebSocket per notifiche push:

```javascript
// src/hooks/useWebSocket.js
export function useWebSocket(url) {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setNotifications(prev => [...prev, data]);
    };
    return () => ws.close();
  }, [url]);

  return notifications;
}
```

### 4. Dashboard Multi-Macchina

Sistema per monitorare più macchine:

```javascript
export function MachineSelector({ machines, onSelect }) {
  return (
    <select onChange={(e) => onSelect(e.target.value)}>
      {machines.map(machine => (
        <option key={machine.id} value={machine.id}>
          {machine.name}
        </option>
      ))}
    </select>
  );
}
```

## 📱 Responsive Design

La dashboard è completamente responsive:

- **Desktop** (1024px+): Layout a 2 colonne
- **Tablet** (640px - 1024px): Layout adattivo
- **Mobile** (< 640px): Layout a singola colonna

## 🐛 Troubleshooting

### Il dashboard non si connette al backend

1. Verifica che FastAPI sia in esecuzione:
   ```bash
   curl http://localhost:8000/health
   ```

2. Controlla i log della console del browser (F12)

3. Verifica la configurazione del proxy in `vite.config.js`

### Gli aggiornamenti non funzionano

1. Controlla che il polling sia attivo (pulsante Play/Pausa)
2. Verifica la connessione OPC UA del backend
3. Controlla i log del server FastAPI

### Errori di build

```bash
# Pulisci e reinstalla
rm -rf node_modules package-lock.json
npm install
```

## 🏗️ Build per Produzione

```bash
npm run build
```

I file ottimizzati saranno generati nella cartella `dist/`.

Per servire in produzione:

```bash
npm run preview
```

## 📚 Tecnologie Utilizzate

- **React 18**: Framework UI
- **Vite**: Build tool e dev server
- **Lucide React**: Icone
- **CSS Variables**: Sistema di theming
- **Fetch API**: Chiamate HTTP

## 📄 Licenza

© 2024 Elco Elettronica Automation Srl

## 👨‍💻 Sviluppo

Per contribuire al progetto:

1. Mantieni la struttura modulare dei componenti
2. Segui le convenzioni di naming esistenti
3. Aggiungi commenti per funzionalità complesse
4. Testa su diversi dispositivi e browser

## 📞 Supporto

Per supporto tecnico, contattare:
- Sito: www.elcoelettronica.it
- Email: [inserire email supporto]
