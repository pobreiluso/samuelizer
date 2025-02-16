from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PromptTemplates:
    DEFAULT_TEMPLATES = {
        "default": {
            "system": "You are an AI specialized in creating concise and comprehensive summaries.",
            "template": """
            Analiza el siguiente texto y genera un resumen estructurado que incluya:

            1. RESUMEN EJECUTIVO (máximo 3 frases)
            - Captura la esencia del mensaje sin detalles innecesarios
            
            2. PUNTOS CLAVE (máximo 5 puntos)
            - Lista solo los puntos verdaderamente importantes
            - Evita redundancias y detalles secundarios
            
            3. ACCIONES REQUERIDAS
            - Lista solo las tareas concretas y accionables
            - Incluye responsable y plazo si se mencionan
            - Omite tareas ambiguas o sin dueño claro

            4. SENTIMIENTO GENERAL (1-2 frases)
            - Tono dominante y cambios significativos
            - Solo si es relevante para el contexto

            Usa lenguaje directo y conciso.
            Evita TODA información redundante o secundaria.
            
            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "executive",
                "format": "structured"
            }
        },

        "executive": {
            "system": "You are an AI specialized in creating executive summaries for business audiences.",
            "template": """
            Genera un resumen ejecutivo estructurado que incluya:

            1. OBJETIVO
            - Propósito principal de la reunión/documento
            
            2. PUNTOS CLAVE
            - Máximo 3 puntos principales, sin detalles innecesarios
            
            3. DECISIONES
            - Decisiones importantes tomadas
            
            4. PRÓXIMOS PASOS
            - Acciones concretas a realizar
            - Responsables (si se mencionan)
            - Plazos (si se especifican)

            5. IMPACTO ESPERADO
            - Resultados o beneficios esperados
            
            Usa lenguaje ejecutivo, directo y orientado a resultados.
            Evita información redundante o detalles técnicos innecesarios.
            
            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "executive",
                "format": "structured"
            }
        },

        "quick": {
            "system": "You are an AI that creates ultra-concise summaries focusing only on essential information.",
            "template": """
            Genera un resumen ultra conciso que incluya SOLO:
            - La idea principal (1 frase)
            - Los puntos críticos (máximo 3 bullets)
            - La conclusión o resultado clave (1 frase)

            Evita TODA información redundante o secundaria.
            Usa lenguaje directo y conciso.
            
            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 200,
                "style": "concise",
                "format": "minimal"
            }
        }
    }

    def __init__(self):
        self.templates = self.DEFAULT_TEMPLATES.copy()
        self.custom_templates = {}

    def get_template(self, template_name: str, **kwargs) -> dict:
        """Obtiene un template con parámetros personalizados"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' no encontrado")
            
        template = self.templates[template_name].copy()
        
        # Actualizar parámetros con los proporcionados
        template["parameters"].update(kwargs)
        
        return template

    def add_custom_template(self, name: str, template: dict):
        """Añade un nuevo template personalizado"""
        required_keys = {"system", "template", "parameters"}
        if not all(key in template for key in required_keys):
            raise ValueError(f"El template debe contener: {required_keys}")
            
        self.custom_templates[name] = template
        self.templates[name] = template

    def modify_template(self, name: str, modifications: dict):
        """Modifica un template existente"""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' no encontrado")
            
        template = self.templates[name]
        for key, value in modifications.items():
            if key in template:
                if isinstance(template[key], dict):
                    template[key].update(value)
                else:
                    template[key] = value
