# 🚀 Propuesta Estratégica — ScrapperGenérico

> **Contexto**: Cuba, sin USD, sin tarjetas de crédito, sin acceso a servicios de pago.
> **Stack 100% gratuito** requerido.
> **Target inicial**: Corredores de casas (Cuba) + Compra/venta mayorista (Cuba)

---

## 📦 Primera propuesta: SISTEMA COMPLETO GRATUITO

### Stack Tecnológico 100% Gratuito

| Componente | Tecnología | Por qué |
|------------|-----------|---------|
| **Backend API** | FastAPI en Hugging Face Spaces (CPU gratis) | Ya lo tenés, funciona, 0 USD |
| **Frontend web** | Gradio (embebido en HF Spaces) | Mismo deploy, 0 USD, interfaz limpia |
| **Base de datos** | SQLite | Ya lo usás, 0 USD, funciona para cientos de usuarios |
| **Bot de mensajería** | Telegram Bot API | **GRATIS TOTAL**, sin límites, sin tarjeta, sin verificación |
| **Scraping** | httpx + BeautifulSoup + requests | 0 USD, corren en CPUs |
| **Calendario / Tareas** | GitHub Actions + cron | 0 USD para repos públicos |
| **Frontend docs / landing** | GitHub Pages | 0 USD, HTML estático |
| **Dominio** | `mitu.hf.space` | Gratis, o Freenom .tk si está disponible |
| **CI/CD** | GitHub Actions | 0 USD |
| **Email** | Ya tenés Gmail SMTP + dotenv | 0 USD |

### Lo que NO podemos usar (requieren tarjeta)

| Servicio | Razón |
|----------|-------|
| ❌ Railway / Fly.io / Render | Requieren tarjeta aunque tengan free tier |
| ❌ AWS / Google Cloud / Azure | Requieren tarjeta |
| ❌ Stripe / Paddle / MercadoPago | Requieren cuenta bancaria/comercio |
| ❌ OpenAI / Claude API | Requieren tarjeta (aunque sean $5) |
| ❌ WhatsApp Business API | Requiere Meta Business Account (complicado desde Cuba) |
| ❌ Playwright | Consume mucha RAM (HF Spaces gratis: 16GB — a veces alcanza, pero es riesgoso) |
| ❌ Supabase / MongoDB Atlas free | Algunos no requieren tarjeta, pero mejor no depender |

---

## 🎯 Target Vertical #1: CORREDORES DE CASAS (Cuba)

### El problema real

En Cuba no existe MLS (Multiple Listing Service). Los corredores usan:
- **Revolico** (classificados, dueños publican directo)
- **Porlalivre** (similar)
- **Telegram** (canales inmensos de ofertas, ej: "Casas en Venta La Habana")
- **Facebook Marketplace / Grupos de Facebook**
- **WhatsApp** (cadenas, grupos)

**El dolor**: Un corredor tiene que revisar 5+ fuentes manualmente, todos los días, para no perder una oportunidad. Cuando aparece una buena propiedad, en minutos ya tiene 20 interesados.

### Solución

Un **bot de Telegram** (gratis, funciona en Cuba, no consume datos pesados):

```
1. Usuario escribe al bot: "casas 3 hab La Habana < 30000 USD"
2. El bot busca en Revolico + Porlalivre + canales de Telegram
3. Devuelve resultados unificados:
   
   🏠 *Resultados para: casas 3 hab La Habana*
   
   📍 *Revolico* — 3 resultados nuevos
   1. Casa 3 hab, Vedado, $28,000 → revoli.co/abc
   2. Casa 3 hab, Miramar, $25,000 → revoli.co/def
   
   📍 *Porlalivre* — 2 resultados nuevos
   1. Casa 3 hab, Centro Habana, $22,000 → pl.co/ghi
   
4. Bot pregunta: "¿Querés que te avise cuando aparezcan nuevas?"
5. Usuario dice "Sí" → el bot monitorea y notifica
```

### Por qué Telegram y NO WhatsApp

| Aspecto | Telegram | WhatsApp |
|---------|----------|----------|
| **Costo** | 100% GRATIS, ilimitado | Requiere Meta Business Account |
| **En Cuba** | ✅ Funciona bien | ✅ Funciona |
| **Bot API** | ✅ Pública, documentada, simple | ❌ Webhook complejo, requiere servidor verificado |
| **Notificaciones** | ✅ Push ilimitadas | ❌ Solo service window (24h) o templates pagados |
| **Archivos** | ✅ Fotos, docs, hasta 2GB | ❌ Limitado |
| **Canales públicos** | ✅ Podés scrapear canales | ❌ No |
| **Programación** | ✅ python-telegram-bot, simple | ❌ httpx + Meta Cloud API, engorroso |

### ¿Qué scrapeamos?

| Fuente | Método | Prioridad |
|--------|--------|-----------|
| **Revolico** — `revolico.com` | HTTP directo + BeautifulSoup | 🔴 Alta |
| **Porlalivre** — `porlalivre.com` | HTTP directo + BeautifulSoup | 🔴 Alta |
| **Canales de Telegram** | `Telegram API` scraping (telethon) o entrada manual | 🟡 Media |
| **Facebook Marketplace Cuba** | Difícil (requiere login, JS) | 🟢 Baja (Fase 2) |

### Monetización (a futuro, cuando haya acceso a pagos)

Mientras tanto, **MVP gratuito que genere valor real**:
- Corredor usa el bot GRATIS
- El bot lleva conteo de búsquedas
- Cuando tengas acceso a pagos (MercadoPago Cuba? Transfermovil?): modelo freemium
- Mientras tanto: el valor está en **tener la base de usuarios y los datos**

---

## 🎯 Target Vertical #2: COMPRA/VENTA MAYORISTA (Cuba)

### El problema real

En Cuba no hay un "MercadoLibre" funcional para mayoristas. La gente compra/vende por:
- **Revolico** (categorías de producto)
- **Grupos de WhatsApp/Telegram** de compra-venta
- **Facebook Marketplace**
- **Porlalivre** (también tiene productos)

**El dolor**: Un revendedor que busca "zapatos talla 42 al por mayor" tiene que revisar decenas de fuentes. Los precios varían mucho, las ofertas aparecen y desaparecen rápido.

### Solución

**El mismo bot de Telegram**, con una vertical adicional:

```
/usar "zapatos talla 42 mayoreo La Habana"
/alertar "zapatos" cada 6h
/precios "zapatos" — muestra precio promedio, mínimo, máximo
```

### ¿Qué scrapeamos?

| Fuente | Método | Prioridad |
|--------|--------|-----------|
| **Revolico** (productos) | HTTP + BS4 | 🔴 Alta |
| **Porlalivre** (productos) | HTTP + BS4 | 🔴 Alta |
| **Telegram canales de compra-venta** | Telethon API | 🟡 Media |

---

## 🏗️ Arquitectura Propuesta (Cuba Stack)

```
┌─────────────────────────────────────────────────────┐
│                 Hugging Face Space                   │
│                                                      │
│  ┌──────────────┐   ┌──────────────────────────┐    │
│  │  FastAPI      │   │  Gradio Frontend         │    │
│  │  (scraping    │   │  - Búsqueda web          │    │
│  │   engine)     │   │  - Dashboard verticales  │    │
│  └──────┬───────┘   │  - Historial             │    │
│         │           └──────────────────────────┘    │
│         ▼                                           │
│  ┌────────────────────────────────────────────┐     │
│  │  Telegram Bot (python-telegram-bot)        │     │
│  │  - /buscar "query"                        │     │
│  │  - /alertar "query" cada N horas          │     │
│  │  - /precios "producto"                    │     │
│  └────────────────────────────────────────────┘     │
│         │                                           │
│         ▼                                           │
│  ┌────────────────────────────────────────────┐     │
│  │  Scraping Engine                           │     │
│  │  - RevolicoAdapter (httpx + BS4)           │     │
│  │  - PorlalivreAdapter (httpx + BS4)         │     │
│  │  - TelegramChannelScraper (telethon)       │     │
│  └────────────────────────────────────────────┘     │
│         │                                           │
│         ▼                                           │
│  ┌────────────────────────────────────────────┐     │
│  │  SQLite (persistencia)                     │     │
│  │  - usuarios_telegram                       │     │
│  │  - busquedas_activas                       │     │
│  │  - resultados_cache                        │     │
│  │  - alertas                                 │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  ┌────────────────────────────────────────────┐     │
│  │  GitHub Actions (cron)                     │     │
│  │  - Alertas cada N horas (healthcheck)      │     │
│  │  - Re-scrape periódico                     │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

---

## 📐 Pipeline de Adaptador Cuba (nuevo formato)

Los adaptadores YAML actuales funcionan para sitios estructurados. Para Cuba necesitamos adaptadores más flexibles. Propongo:

```yaml
# adapters/revolico_casas.yaml
name: revolico_casas
site: revolico.com
vertical: real_estate_cuba
country: cuba
search_url: "https://www.revolico.com/search/{query}?page={page}"
container_selector: "article.result-item"     # <-- selectores reales de Revolico
fields:
  - name: titulo
    selector: "h2.title a"
    type: text
  - name: precio
    selector: "span.price"
    type: price
  - name: ubicacion
    selector: "span.location"
    type: text
  - name: url
    selector: "h2.title a"
    type: url
    attribute: href
  - name: fecha
    selector: "span.date"
    type: text
canonical_map:
  title: titulo
  price: precio
  location: ubicacion
  url: url
  date: fecha
```

Y para Telegram:
```yaml
# adapters/telegram_casas_habana.yaml
name: telegram_casas_habana
site: telegram
vertical: real_estate_cuba
country: cuba
telegram_channel: "@CasasEnVentaLaHabana"   # <-- nuevo campo
search_fields:
  - titulo
  - precio
  - ubicacion
```

---

## 📋 Plan de Implementación (Fase Cuba 1 — MVP)

### Semana 1: Fundación
1. ✅ Arreglar los 3 tests fallando (bugs existentes)
2. ⬜ Commitear el progreso actual de Fase 2
3. ⬜ Crear adapter real para Revolico (inspeccionar HTML real)
4. ⬜ Crear adapter real para Porlalivre

### Semana 2: Telegram Bot
5. ⬜ Integrar `python-telegram-bot` en el proyecto
6. ⬜ Comando `/buscar` que usa el search engine existente
7. ⬜ Comando `/start` con bienvenida y onboarding
8. ⬜ Desplegar en HF Spaces con Gradio + Bot

### Semana 3: Alertas
9. ⬜ Comando `/alertar` con intervalo configurable
10. ⬜ Sistema de cache (no repetir resultados ya vistos)
11. ⬜ GitHub Actions para healthcheck y rescrape periódico

### Semana 4: Pulido
12. ⬜ Comando `/precios` (stats básicos)
13. ⬜ Landing page en GitHub Pages
14. ⬜ Probar con 1-2 corredores de casas reales en Cuba

---

## 💡 Otras Ideas Low-Tech para Cuba

### Opción offline / baja conectividad
Si internet en Cuba es el bottleneck (ETECSA, datos móviles caros):
- El bot de Telegram funciona con **texto plano**, consume < 1KB por mensaje
- Las búsquedas se hacen del lado del servidor (HF Spaces)
- El usuario solo recibe texto → **mínimo consumo de datos**

### Opción SMS (cuando Telegram no esté disponible)
- Cuba tiene buena cobertura SMS
- Hay APIs de SMS gratuitas (Twilio no, pero algunas locales)
- **Postergado**: el SMS es más complejo y caro que Telegram

### Opcion "corredor power user"
- Además del bot, ofrecer un **panel web** (Gradio) donde el corredor vea en una pantalla todas las ofertas de todas las fuentes
- Ideal para el que tiene WiFi en casa (Nauta)

---

## ⚠️ Riesgos y Mitigaciones (contexto Cuba)

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Revolico cambia HTML | Alta | Tests de integración que detectan cambios |
| HF Spaces se duerme (free tier) | Alta | GitHub Actions cada 30min hace ping |
| Internet inestable en Cuba | Alta | Bot funciona con mensajes de texto (mínimo ancho de banda) |
| Telegram bloqueado en Cuba | Baja (hoy) | Tener plan B con SMS o web app |
| ETECSA bloquea el scraping | Baja | Rate limiting, respetar robots.txt |

---

## 🧪 Lo que YA tenemos que sirve

| Recurso | Estado | Para qué sirve en Cuba |
|---------|--------|----------------------|
| FastAPI + Orchestrator | ✅ Listo | Backend del bot y la web |
| AdapterLoader YAML | ✅ Listo | Cargar adaptadores de Cuba |
| ResultNormalizer | ⚠️ Con bugs | Unificar resultados de Revolico, Porlalivre, Telegram |
| Endpoint `/api/search` | ✅ Creado | Motor de búsqueda multi-fuente |
| SQLite | ✅ Listo | Guardar usuarios, búsquedas, cache |
| GitHub CI | ✅ Listo | Build + test |
| Gmail SMTP | ✅ Listo | Notificaciones por email (alternativa al bot) |

---

## 📌 Conclusión

**El proyecto es viable 100% gratis.** La clave está en:

1. **Telegram Bot como interfaz principal** — es lo que funciona en Cuba, es gratis, es liviano
2. **Revolico + Porlalivre como fuentes iniciales** — son los clasificados más grandes de Cuba
3. **HF Spaces + SQLite como backend** — cero costo, cero tarjeta
4. **Agregar valor con alertas y unificación** — el corredor deja de revisar 5 sitios

**No necesitamos USD para construir el MVP.** Necesitamos USD cuando queramos monetizar (y para entonces habrá opciones como Transfermovil, QR desde el exterior, o MercadoPago Cuba si algún día llega).

---

*Próxima sesión: Arreglar bugs → commitear → adapter Revolico real → bot de Telegram*
