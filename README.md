
# Diagnóstico de Errores IG Global v2 (Reasoning Engine)

Agente multimodal desplegado en **Vertex AI Reasoning Engine** para el diagnóstico automatizado de errores mediante análisis de captura de pantalla y consultas en texto.

## Características
* **Scraper dinámico**: Scraping en tiempo real del FAQ oficial de IG Global con caché inteligente de 10 minutos.
* **Modelo Gemini Multimodal**: Análisis visual de capturas de pantalla (`gemini-3.8-flash`).
* **Lógica de Derivación**: Clasifica entre errores solucionables (Respuestas automáticas) y errores no indexados (`[[DERIVAR_CANALIZADOR]]`).
* **Zonas horarias**: Saludos adaptados según el horario de Argentina (`America/Argentina/Buenos_Aires`).

## Despliegue en GCP
1. Autenticarse en Google Cloud:
   ```bash
   gcloud auth application-default login