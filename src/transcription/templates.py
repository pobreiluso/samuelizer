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
            "system": "You are an AI specialized in creating executive summaries with clear structure and visual appeal.",
            "template": """
            Genera un resumen ejecutivo estructurado:

            🎯 Objetivo
            • Propósito principal de la reunión/documento
            
            💡 Puntos clave
            • Máximo 3 puntos esenciales
            • **Sin detalles innecesarios**
            
            ✨ Decisiones
            • Lista de decisiones importantes
            • Destaca el **impacto** de cada una
            
            📋 Próximos pasos
            • [ ] Acciones concretas
            • [ ] @Responsables
            • [ ] 📅 Plazos
            
            🚀 Impacto esperado
            • Resultados y beneficios clave
            • Métricas relevantes
            
            Usa formato markdown para resaltar elementos importantes:
            - Usa **negrita** para énfasis
            - Usa `código` para referencias técnicas
            - Usa > para citas importantes
            
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
            "system": "You are an AI that creates ultra-concise summaries with visual appeal.",
            "template": """
            Genera un resumen ultra conciso:

            💫 **Idea principal**
            • Una frase que capture la esencia

            🎯 **Puntos críticos**
            • Máximo 3 bullets
            • Solo lo verdaderamente importante
            
            ✨ **Conclusión clave**
            • Una frase con el resultado principal

            Usa formato markdown para resaltar elementos importantes.
            Evita toda información secundaria.
            
            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 200,
                "style": "concise",
                "format": "minimal"
            }
        },

        "slack": {
            "system": "You are an AI specialized in analyzing and summarizing Slack conversations in a concise and actionable way.",
            "template": """
            Lee y analiza la siguiente conversación de Slack.
            Proporciona un resumen estructurado y conciso que incluya:

            PRINCIPALES TEMAS:
            - Identifica y lista los temas principales (máximo 3-4)
            - Para cada tema, proporciona 2-3 oraciones que capturen lo esencial
            - Enfócate en decisiones, problemas y soluciones

            TAREAS Y RESPONSABLES:
            - Lista solo las tareas concretas y accionables
            - Incluye responsable y plazo (si se mencionan)
            - Omite tareas ambiguas o sin asignación clara

            CONCLUSIÓN GENERAL:
            - Resume el propósito principal de la conversación
            - Destaca las siguientes acciones a tomar
            - Menciona cualquier decisión final importante

            Instrucciones:
            - Sé conciso pero no omitas información crítica
            - Prioriza información para seguimiento
            - El resumen debe ser más corto que el contenido original
            - Usa lenguaje claro y directo

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 600,
                "style": "concise",
                "format": "structured",
                "preserve_mentions": True
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
