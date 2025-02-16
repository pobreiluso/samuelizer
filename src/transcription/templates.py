from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PromptTemplates:
    DEFAULT_TEMPLATES = {
        "summary": {
            "system": "You are an AI summarize into a concise abstract paragraph.",
            "template": """
            Analiza el siguiente texto y genera un resumen conciso que capture:
            - El contexto y propósito principal
            - Los puntos más importantes discutidos
            - Las conclusiones o resultados clave
            
            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 500,
                "style": "professional"
            }
        },
        
        "key_points": {
            "system": "You are an AI identify and list the main points.",
            "template": """
            Identifica y lista los puntos principales del siguiente texto.
            Para cada punto:
            - Debe ser una idea completa y autocontenida
            - Debe ser relevante para el tema principal
            - Debe estar expresado de forma clara y concisa

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_points": 10,
                "format": "bullet_points"
            }
        },
        
        "action_items": {
            "system": "You are an AI extract action items.",
            "template": """
            Extrae los elementos accionables del siguiente texto.
            Para cada acción:
            - Debe ser una tarea concreta
            - Debe identificar responsables (si se mencionan)
            - Debe incluir plazos o fechas límite (si se mencionan)
            - Debe estar en formato de tarea

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "format": "tasks",
                "include_owners": True,
                "include_deadlines": True
            }
        },
        
        "sentiment": {
            "system": "You are an AI analyze the sentiment of the following text.",
            "template": """
            Realiza un análisis de sentimiento del siguiente texto considerando:
            - Tono general de la conversación
            - Cambios de sentimiento durante el texto
            - Reacciones a temas específicos
            - Nivel de acuerdo/desacuerdo entre participantes

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "detail_level": "detailed",
                "include_quotes": True
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
