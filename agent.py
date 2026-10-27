
"""
Diagnóstico de Errores IG Global v2 - Reasoning Engine
Agent for Vertex AI Reasoning Engine that analyzes error screenshots/queries against a live FAQ.
"""

import base64
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# URL de la base de conocimiento oficial
FAQ_URL = "https://igglobal.net/help/faq/errores/"

# Instrucciones del sistema para Gemini
SYSTEM_PROMPT = """Eres el Asistente Especialista en Diagnóstico de Errores para la plataforma IG Global / Global ERP.
Analizas capturas de pantalla o reportes de errores de los usuarios y brindas una solución concreta basada ÚNICAMENTE en la base de conocimiento que se te entrega en cada consulta (FAQ oficial de errores).

CÓMO IDENTIFICAR EL ERROR:
- Compara el número de error, el mensaje y el origen (ej. "pg_Generar_Comprobante_Ventas", "Lg_IngresoUsuario") de la captura con las entradas de la base. El mensaje puede estar truncado o variar levemente.
- Si hay más de un caso posible, elige el más específico.

CASO A: EL ERROR ESTÁ EN LA BASE Y TIENE SOLUCIÓN. Estructura de la respuesta (SIN PREGUNTAS ABIERTAS):
1. Saludo: usa exactamente el saludo indicado en el mensaje (ej. "Hola Christian, buenas tardes.").
2. Explicación técnica y solución: causa y pasos de resolución, claros y al grano, tal como figuran en la base. No agregues pasos que no estén en ella.
3. Cierre: NUNCA hagas preguntas ni esperes respuesta en este hilo. Cierra con: "En caso de requerir asistencia adicional con este u otro tema, por favor genera un nuevo ticket de soporte."
4. Enlace: adjunta SIEMPRE al final la URL oficial: __FAQ_URL__

CASO B: EL ERROR ESTÁ EN LA BASE PERO NO TRAE SOLUCIÓN UTILIZABLE (solo remite a una imagen o a un enlace que no tienes): explica la causa que sí figura, indica que la consulta será derivada a Soporte Técnico, y mantén saludo, cierre y enlace como en el caso A. No inventes pasos.

CASO C: LA CAPTURA O CONSULTA NO CORRESPONDE A NINGÚN ERROR DE LA BASE (por ejemplo, otro módulo, importador, exportador, un error nuevo, o una captura sin error):
- NO respondas al usuario ni inventes soluciones.
- Responde ÚNICAMENTE con este formato:
[[DERIVAR_CANALIZADOR]]
Descripción objetiva de lo que ves: pantalla o módulo, número de error si lo hay, texto exacto del mensaje, y cualquier dato visible relevante (nombre del proceso, origen, campos).
- Sin saludo, sin cierre, sin enlace y sin soluciones.

TONO: directo y conciso, sin divagar."""


class SoftwareBugAssistantEngine:
    """Clase del Agente compatible con Vertex AI Reasoning Engine."""

    def __init__(self, project: str, model_name: str = "gemini-3.8-flash"):
        self.project = project
        self.model_name = model_name
        self._faq_text = None
        self._faq_time = 0

    def _get_faq(self) -> str:
        """Lee el FAQ en vivo (caché de 10 min). Si falla, usa la última copia en memoria."""
        if self._faq_text and time.time() - self._faq_time < 600:
            return self._faq_text

        try:
            r = requests.get(FAQ_URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            text = BeautifulSoup(r.text, "html.parser").get_text("\n")
            text = re.sub(r"\n\s*\n+", "\n", text)
            
            ini = text.find("0001.")
            fin = text.find("TagsCloud")
            if ini != -1:
                text = text[ini: fin if fin > ini else len(text)]
            
            if len(text) > 2000:
                self._faq_text, self._faq_time = text, time.time()
                return text
        except Exception:
            pass

        return self._faq_text or ""

    def query(
        self,
        prompt: str,
        image_bytes: str = None,
        mime_type: str = "image/png",
        user_name: str = ""
    ) -> str:
        """
        Método invocado por Vertex AI Reasoning Engine.
        
        Args:
            prompt: Texto o consulta del usuario.
            image_bytes: Imagen codificada en Base64 o bytes crudos.
            mime_type: Tipo MIME de la imagen (ej. image/png, image/jpeg).
            user_name: Nombre del usuario para personalización de saludo.
        """
        # Formatear saludo dinámico
        hora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).hour
        momento = "buenos días" if hora < 12 else ("buenas tardes" if hora < 20 else "buenas noches")
        nombre = user_name.strip().split()[0].capitalize() if user_name and user_name.strip() else ""
        saludo = f"Hola {nombre}, {momento}." if nombre else f"Hola, {momento}."

        # Obtener base de conocimiento actualizada
        faq = self._get_faq()
        if faq:
            base = "BASE DE CONOCIMIENTO (FAQ oficial de errores):\n" + faq
        else:
            base = (
                "BASE DE CONOCIMIENTO: no disponible en este momento. "
                "Aplica el CASO C (derivar al canalizador)."
            )

        # Inicializar cliente GenAI de Vertex AI
        client = genai.Client(vertexai=True, project=self.project, location="global")

        contents = [f"Saludo a usar: {saludo}\n\n{base}\n\nConsulta del usuario: {prompt}"]
        
        if image_bytes:
            raw = base64.b64decode(image_bytes) if isinstance(image_bytes, str) else image_bytes
            contents.append(types.Part.from_bytes(data=raw, mime_type=mime_type))

        # Generar respuesta con Gemini
        response = client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT.replace("__FAQ_URL__", FAQ_URL),
                temperature=0.2,
            ),
        )
        return response.text