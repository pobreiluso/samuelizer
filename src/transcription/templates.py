from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PromptTemplates:
    DEFAULT_TEMPLATES = {
        "summary": {
            "system": "You are an AI summarize into a concise abstract paragraph.",
            "template": """
            Analyze the following text and generate a concise summary that captures:
            - The context and main purpose
            - The most important points discussed
            - Key conclusions or results
            
            Text to analyze:
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
            Identify and list the main points from the following text.
            For each point:
            - Must be a complete and self-contained idea
            - Must be relevant to the main topic
            - Must be expressed clearly and concisely

            Text to analyze:
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
            Extract actionable items from the following text.
            For each action:
            - Must be a concrete task
            - Must identify owners (if mentioned)
            - Must include deadlines (if mentioned)
            - Must be in task format

            Text to analyze:
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
            Perform a sentiment analysis of the following text considering:
            - General tone of the conversation
            - Sentiment changes throughout the text
            - Reactions to specific topics
            - Level of agreement/disagreement between participants

            Text to analyze:
            {text}
            """,
            "parameters": {
                "detail_level": "detailed",
                "include_quotes": True
            }
        },

        "default": {
            "system": "You are an AI specialized in creating concise and comprehensive summaries with a friendly and visually appealing format.",
            "template": """
            Analyze the following text and generate a structured summary including:

            📝 Executive Summary
            • Capture the message essence in max 3 sentences
            • Use clear and direct language
            
            ⭐️ Key Points
            • List only truly important points
            • Each point must provide unique value
            • Use bullets for better readability
            
            ✅ Action Items
            • [ ] Concrete and actionable tasks
            • [ ] Include @owner and 📅 deadline if mentioned
            • [ ] Skip tasks without clear owner

            💭 Sentiment
            • General tone and relevant changes
            • Only if it provides important context

            Use markdown format to highlight important elements:
            - Use **bold** for emphasis
            - Use `code` for technical references
            - Use > for important quotes
            
            Text to analyze:
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

        "slack_brief": {
            "system": "You are an AI that creates ultra-concise Slack conversation summaries focusing only on decisions and actions.",
            "template": """
            Analiza esta conversación de Slack y genera un resumen ultra conciso:

            📍 **TL;DR**
            • La esencia en una frase

            🎯 **Decisiones**
            • Solo decisiones finales tomadas
            • Sin contexto ni discusiones

            ⚡️ **Pendiente**
            • [ ] Solo tareas NO completadas
            • [ ] Con @responsable si existe

            Reglas:
            - Máxima brevedad
            - Solo info CRÍTICA
            - Ignorar discusiones/debates
            - Omitir todo lo que no sea decisión/acción
            - Usar emojis estratégicamente

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 250,
                "style": "minimal",
                "format": "bullet",
                "preserve_mentions": True
            }
        },

        "slack_detailed": {
            "system": "You are an AI that creates structured summaries of Slack conversations with focus on context and outcomes.",
            "template": """
            Analiza esta conversación de Slack y genera un resumen estructurado:

            📌 **Contexto**
            • Tema central
            • Participantes clave

            💡 **Discusiones Principales**
            • Tema → Conclusión
            • Solo debates relevantes
            • Incluir puntos de desacuerdo importantes

            ✅ **Decisiones Finales**
            • Qué se decidió
            • Por qué se decidió
            • Impacto esperado

            📋 **Plan de Acción**
            • [ ] Tareas pendientes (@responsable)
            • [ ] Próximos pasos
            • [ ] Fechas clave

            ⚠️ **Puntos de Atención**
            • Bloqueantes/Riesgos
            • Dependencias externas
            • Recursos necesarios

            Reglas:
            - Mantener contexto relevante
            - Destacar desacuerdos importantes
            - Enfatizar decisiones y razones
            - Incluir @menciones y #canales
            - Usar emojis para mejorar lectura

            Texto a analizar:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "structured",
                "format": "detailed",
                "preserve_mentions": True,
                "include_context": True
            }
        },

        "one_to_one": {
            "system": "You are an AI specialized in analyzing and summarizing 1:1 meetings with Tech Leads.",
            "template": """
            Analyze this 1:1 meeting and provide a structured summary following this format:

            🚦 **Daily Challenges & Blockers**
            • Technical and process blockers
            • Time management issues
            • Team coordination challenges

            🎯 **Team Performance**
            • Current team status
            • Key achievements
            • Areas needing attention

            📋 **Resource Needs**
            • Tools and resources required
            • Training needs
            • Support requirements

            💡 **Improvement Areas**
            • Process improvements
            • Technical improvements
            • Team dynamics improvements

            👥 **Guild & Career Development**
            • Guild participation and impact
            • Training progress and plans
            • Career path discussion
            • Knowledge sharing initiatives

            👤 **Personal Development**
            • Salary expectations
            • Career expectations
            • Work-life balance
            • Job satisfaction

            ⚡️ **Action Items**
            • [ ] Concrete next steps
            • [ ] Assigned responsibilities
            • [ ] Follow-up items

            Use markdown format to highlight important elements:
            - Use **bold** for emphasis
            - Use > for important quotes
            - Use bullet points for better readability

            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "structured",
                "format": "detailed",
                "include_action_items": True
            }
        },

        "weekly_sync": {
            "system": "You are an AI specialized in analyzing and summarizing weekly team sync meetings.",
            "template": """
            Analyze this weekly sync meeting and provide a structured summary following this format:

            📅 **Last Week's Achievements**
            • List completed tasks and milestones
            • Highlight significant progress
            • Note any resolved issues
            • Include metrics when available

            📋 **This Week's Plan**
            • Outline planned tasks and goals
            • Prioritize key deliverables
            • Mention ongoing projects
            • Include deadlines if specified

            🚧 **Blockers & Risks**
            • Current blockers
            • Potential risks
            • Dependencies
            • Resource constraints

            ⚡️ **Action Items**
            • [ ] Concrete tasks with owners
            • [ ] Follow-up items
            • [ ] Decisions that need to be made
            • [ ] Dependencies to be resolved

            Use markdown format to highlight important elements:
            - Use **bold** for emphasis
            - Use > for important quotes
            - Use bullet points for better readability
            - Include @mentions for ownership

            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "structured",
                "format": "detailed",
                "include_action_items": True
            }
        },

        "auto": {
            "system": """You are an AI expert in content analysis and template selection.
            Your task is to analyze the given text and determine the most appropriate template
            for summarizing it based on its content, structure, and context.""",
            "template": """
            Analyze this text and determine the most appropriate template to use for summarization.
            Consider these aspects:

            1. Content Type:
            - Is it a meeting? What kind? (1:1, team sync, presentation)
            - Is it a Slack conversation?
            - Is it a general document or transcript?

            2. Content Structure:
            - How formal/informal is it?
            - Is it structured or free-flowing?
            - Are there clear sections or topics?

            3. Content Elements:
            - Are there action items?
            - Are there decisions made?
            - Is there technical discussion?
            - Is there personal/career discussion?

            Available templates:
            - one_to_one: For 1:1 meetings with focus on personal/career development
            - weekly_sync: For team status updates and planning
            - executive: For formal meetings with clear structure
            - quick: For brief, informal discussions
            - slack_brief: For Slack conversations needing minimal context
            - slack_detailed: For complex Slack discussions
            - summary: For general content requiring standard summary
            - action_items: For content focused on tasks and actions
            - sentiment: For content where tone and reactions matter

            Text to analyze:
            {text}

            Respond with:
            1. The recommended template name
            2. A brief explanation of why this template is most appropriate
            3. Any specific considerations for using this template
            """
        }
    }

    def __init__(self):
        self._templates = self.DEFAULT_TEMPLATES.copy()
        self._custom_templates = {}
        self._template_cache = {}
        
    @property
    def templates(self):
        """Read-only access to templates"""
        return self._templates.copy()

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
