# SPEC-NOTIFICATIONS-001: Sistema de Notificaciones Centralizado

**Fecha:** 2026-04-12  
**Estado:** 📋 Propuesta  
**Prioridad:** Alta  
**Estimación:** 3-4 horas

---

## 🎯 Objetivo

Implementar un sistema de notificaciones centralizado para monitorear en tiempo real:
- Progreso de scraping
- Ejecución de analytics
- Detección de oportunidades
- Errores y alertas del sistema

---

## 📊 Contexto

**Problema actual:**
- No hay visibilidad del progreso de tareas en tiempo real
- Los logs solo están disponibles vía Docker logs
- No hay notificaciones cuando se detectan oportunidades
- Difícil saber cuándo operar después de un scraping

**Necesidad:**
> "Necesito conocer el progreso del scraping en todo momento para saber cuándo operar"

---

## 🏗️ Arquitectura Propuesta

### 1. Backend: Sistema de Eventos

```python
# notifications/event_bus.py
from enum import Enum
from typing import Dict, Any, List, Callable
from datetime import datetime
import json

class EventType(Enum):
    SCRAPING_STARTED = "scraping.started"
    SCRAPING_PROGRESS = "scraping.progress"
    SCRAPING_COMPLETED = "scraping.completed"
    SCRAPING_ERROR = "scraping.error"
    
    ANALYTICS_STARTED = "analytics.started"
    ANALYTICS_PROGRESS = "analytics.progress"
    ANALYTICS_COMPLETED = "analytics.completed"
    
    OPPORTUNITY_DETECTED = "opportunity.detected"
    OPPORTUNITY_HIGH_SCORE = "opportunity.high_score"  # Score > 80
    
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"

class Event:
    def __init__(self, event_type: EventType, data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data
        self.timestamp = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

class EventBus:
    """Singleton event bus for pub/sub notifications"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subscribers = {}
            cls._instance.event_history = []
        return cls._instance
    
    def publish(self, event: Event):
        """Publish event to all subscribers"""
        self.event_history.append(event)
        
        # Notify subscribers
        for subscriber in self.subscribers.get(event.type, []):
            subscriber(event)
        
        # Notify wildcard subscribers
        for subscriber in self.subscribers.get('*', []):
            subscriber(event)
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
```

### 2. Persistencia: Tabla de Notificaciones

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(36) UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',  -- info, warning, error, success
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_type ON notifications(event_type);
CREATE INDEX idx_notifications_read ON notifications(read);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);
```

### 3. WebSocket para Tiempo Real

```python
# api/websocket.py
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to notification server'})

@socketio.on('subscribe')
def handle_subscribe(data):
    room = data.get('event_type', 'all')
    join_room(room)
    emit('subscribed', {'room': room})

# Event handler
def broadcast_event(event: Event):
    socketio.emit('notification', event.to_dict(), room=event.type.value)
    socketio.emit('notification', event.to_dict(), room='all')

# Subscribe to event bus
event_bus = EventBus()
event_bus.subscribe('*', broadcast_event)
```

### 4. Frontend: Componente de Notificaciones

```javascript
// static/js/notifications.js
class NotificationManager {
    constructor() {
        this.socket = io();
        this.notifications = [];
        this.setupSocketListeners();
    }
    
    setupSocketListeners() {
        this.socket.on('notification', (event) => {
            this.addNotification(event);
            this.showToast(event);
            this.updateBadge();
        });
    }
    
    showToast(event) {
        // Toast notification en la UI
        const toast = document.createElement('div');
        toast.className = `toast toast-${event.data.severity}`;
        toast.innerHTML = `
            <strong>${event.data.title}</strong>
            <p>${event.data.message}</p>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
    
    updateBadge() {
        const unread = this.notifications.filter(n => !n.read).length;
        document.querySelector('.notification-badge').textContent = unread;
    }
}
```

---

## 🔧 Integración con Scraper

```python
# scraper_selenium.py
from notifications.event_bus import EventBus, Event, EventType

class PortalInmobiliarioSeleniumScraper:
    def __init__(self, operacion, tipo, headless=True):
        # ... existing code ...
        self.event_bus = EventBus()
    
    def scrape_all_pages(self, max_pages=None):
        # Emit start event
        self.event_bus.publish(Event(
            EventType.SCRAPING_STARTED,
            {
                'severity': 'info',
                'title': 'Scraping Iniciado',
                'message': f'Scraping {self.operacion} - {self.tipo}',
                'operacion': self.operacion,
                'tipo': self.tipo,
                'max_pages': max_pages
            }
        ))
        
        try:
            # ... scraping logic ...
            
            # Emit progress
            self.event_bus.publish(Event(
                EventType.SCRAPING_PROGRESS,
                {
                    'severity': 'info',
                    'title': 'Progreso de Scraping',
                    'message': f'Página {page}/{max_pages} - {len(properties)} propiedades',
                    'page': page,
                    'total_pages': max_pages,
                    'properties_count': len(properties),
                    'progress_pct': (page / max_pages) * 100
                }
            ))
            
            # Emit completion
            self.event_bus.publish(Event(
                EventType.SCRAPING_COMPLETED,
                {
                    'severity': 'success',
                    'title': 'Scraping Completado',
                    'message': f'{total_properties} propiedades scrapeadas',
                    'total_properties': total_properties,
                    'duration_seconds': duration
                }
            ))
            
        except Exception as e:
            # Emit error
            self.event_bus.publish(Event(
                EventType.SCRAPING_ERROR,
                {
                    'severity': 'error',
                    'title': 'Error en Scraping',
                    'message': str(e),
                    'error_type': type(e).__name__
                }
            ))
```

---

## 🔧 Integración con Analytics

```python
# analytics.py
def run_analytics_pipeline():
    event_bus = EventBus()
    
    event_bus.publish(Event(
        EventType.ANALYTICS_STARTED,
        {
            'severity': 'info',
            'title': 'Analytics Iniciado',
            'message': 'Ejecutando pipeline de analytics'
        }
    ))
    
    # ... analytics logic ...
    
    # Notify high-score opportunities
    for opp in high_score_opportunities:
        event_bus.publish(Event(
            EventType.OPPORTUNITY_HIGH_SCORE,
            {
                'severity': 'success',
                'title': '🎯 Oportunidad Excelente Detectada',
                'message': f'{opp.titulo} - Score: {opp.score}',
                'opportunity_id': opp.id,
                'score': opp.score,
                'url': opp.property.url
            }
        ))
```

---

## 📱 Canales de Notificación

### 1. In-App (Prioridad 1)
- ✅ WebSocket en tiempo real
- ✅ Toast notifications
- ✅ Badge de notificaciones no leídas
- ✅ Panel de historial

### 2. Email (Prioridad 2)
```python
# notifications/email_notifier.py
def send_email_notification(event: Event):
    if event.type == EventType.OPPORTUNITY_HIGH_SCORE:
        send_email(
            to=config.NOTIFICATION_EMAIL,
            subject=f"🎯 Nueva Oportunidad - Score {event.data['score']}",
            body=render_template('email/opportunity.html', event=event)
        )
```

### 3. Webhook (Prioridad 3)
```python
# notifications/webhook_notifier.py
def send_webhook(event: Event):
    if config.WEBHOOK_URL:
        requests.post(config.WEBHOOK_URL, json=event.to_dict())
```

### 4. Telegram/WhatsApp (Futuro)
- Integración con Telegram Bot API
- Notificaciones push móviles

---

## 🎨 UI Propuesta

### Notification Bell (Header)
```html
<div class="notification-bell">
    <i class="fas fa-bell"></i>
    <span class="badge">3</span>
</div>

<div class="notification-dropdown">
    <div class="notification-item unread">
        <span class="severity-badge success">✓</span>
        <div class="content">
            <strong>Scraping Completado</strong>
            <p>144 propiedades scrapeadas</p>
            <small>Hace 2 minutos</small>
        </div>
    </div>
</div>
```

### Progress Bar (Durante Scraping)
```html
<div class="scraping-progress">
    <div class="progress-header">
        <span>Scraping en progreso...</span>
        <span>Página 2/10</span>
    </div>
    <div class="progress-bar">
        <div class="progress-fill" style="width: 20%"></div>
    </div>
    <div class="progress-stats">
        <span>96 propiedades</span>
        <span>~8 min restantes</span>
    </div>
</div>
```

---

## 📋 Tareas de Implementación

### Fase 1: Backend Core (2h)
- [ ] Crear `notifications/event_bus.py`
- [ ] Crear modelo `Notification` en SQLAlchemy
- [ ] Migración de BD para tabla `notifications`
- [ ] API endpoints:
  - `GET /api/v2/notifications` - Listar notificaciones
  - `POST /api/v2/notifications/:id/read` - Marcar como leída
  - `DELETE /api/v2/notifications/:id` - Eliminar

### Fase 2: WebSocket (1h)
- [ ] Instalar `flask-socketio`
- [ ] Configurar WebSocket server
- [ ] Integrar con EventBus

### Fase 3: Integración (1h)
- [ ] Integrar en `scraper_selenium.py`
- [ ] Integrar en `analytics.py`
- [ ] Integrar en `scheduler.py`

### Fase 4: Frontend (1h)
- [ ] Componente de notificaciones
- [ ] Toast notifications
- [ ] Panel de historial
- [ ] Progress bars

---

## 🧪 Testing

```python
# tests/test_notifications.py
def test_event_bus():
    bus = EventBus()
    received = []
    
    def handler(event):
        received.append(event)
    
    bus.subscribe(EventType.SCRAPING_STARTED, handler)
    bus.publish(Event(EventType.SCRAPING_STARTED, {'test': True}))
    
    assert len(received) == 1
    assert received[0].data['test'] is True
```

---

## 📊 Métricas

- **Latencia de notificación:** < 100ms
- **Retención de eventos:** 7 días
- **Conexiones WebSocket concurrentes:** 10+

---

## 🔄 Próximos Pasos

1. Aprobar especificación
2. Implementar Fase 1 (Backend Core)
3. Testing básico
4. Implementar Fase 2-4
5. Deploy y monitoreo

---

## 📝 Notas

- Usar Redis para pub/sub en producción (escalabilidad)
- Considerar rate limiting para evitar spam de notificaciones
- Implementar filtros de notificaciones por usuario
