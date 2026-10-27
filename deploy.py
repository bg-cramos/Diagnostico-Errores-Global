
"""
Script para empaquetar y desplegar / actualizar el agente en Vertex AI Reasoning Engine.
"""

import vertexai
from vertexai.preview import reasoning_engines
from agent import SoftwareBugAssistantEngine

# Configuración del Proyecto GCP
PROJECT_ID = "ig-cloud-47839"
LOCATION = "us-west1"
STAGING_BUCKET = "gs://ig-cloud-47839-reasoning-staging"

def deploy():
    print("Inicializando SDK de Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)

    print("Instanciando agente de diagnóstico...")
    agent_instance = SoftwareBugAssistantEngine(
        project=PROJECT_ID,
        model_name="gemini-3.8-flash"
    )

    print("Desplegando en Reasoning Engine...")
    remote_agent = reasoning_engines.ReasoningEngine.create(
        agent_instance,
        requirements=[
            "google-genai",
            "requests",
            "beautifulsoup4",
            "tzdata"
        ],
        display_name="Diagnostico Errores IG Global v2",
        description="Diagnostico por FAQ en vivo; deriva al canalizador si no hay coincidencia.",
    )

    print(f"\n¡Agente desplegado con éxito!")
    print(f"Resource Name: {remote_agent.resource_name}")

if __name__ == "__main__":
    deploy()