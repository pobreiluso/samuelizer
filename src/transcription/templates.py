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
            Generate a structured executive summary:

            🎯 Objective
            • Main purpose of the meeting/document
            
            💡 Key Points
            • Maximum 3 essential points
            • **No unnecessary details**
            
            ✨ Decisions
            • List of important decisions
            • Highlight the **impact** of each one
            
            📋 Next Steps
            • [ ] Concrete actions
            • [ ] @Responsible persons
            • [ ] 📅 Deadlines
            
            🚀 Expected Impact
            • Key results and benefits
            • Relevant metrics
            
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

        "quick": {
            "system": "You are an AI that creates ultra-concise summaries with visual appeal.",
            "template": """
            Generate an ultra-concise summary:

            💫 **Main Idea**
            • A single sentence capturing the essence

            🎯 **Critical Points**
            • Maximum 3 bullet points
            • Only what is truly important
            
            ✨ **Key Conclusion**
            • One sentence with the main result

            Use markdown format to highlight important elements.
            Avoid all secondary information.
            
            Text to analyze:
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
            Analyze this Slack conversation and generate an ultra-concise summary:

            📍 **TL;DR**
            • The essence in one sentence

            🎯 **Decisions**
            • Only final decisions made
            • No context or discussions

            ⚡️ **Pending**
            • [ ] Only tasks NOT completed
            • [ ] With @responsible person if available

            Rules:
            - Maximum brevity
            - Only CRITICAL info
            - Ignore discussions/debates
            - Omit everything that is not a decision/action
            - Use emojis strategically

            Text to analyze:
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
            Analyze this Slack conversation and generate a structured summary:

            📌 **Context**
            • Central topic
            • Key participants

            💡 **Main Discussions**
            • Topic → Conclusion
            • Only relevant debates
            • Include important points of disagreement

            ✅ **Final Decisions**
            • What was decided
            • Why it was decided
            • Expected impact

            📋 **Action Plan**
            • [ ] Pending tasks (@responsible person)
            • [ ] Next steps
            • [ ] Key dates

            ⚠️ **Points of Attention**
            • Blockers/Risks
            • External dependencies
            • Required resources

            Rules:
            - Maintain relevant context
            - Highlight important disagreements
            - Emphasize decisions and reasons
            - Include @mentions and #channels
            - Use emojis to improve readability

            Text to analyze:
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

        "brainstorming": {
            "system": "You are an AI specialized in capturing and organizing ideas from chaotic brainstorming sessions where multiple people speak simultaneously and ideas flow rapidly without structure.",
            "template": """
            Analyze this brainstorming session and extract all valuable ideas, even those mentioned briefly or incompletely. Organize them in the following format:

            🌟 **Core Problem/Challenge**
            • Identify the central problem or challenge being addressed
            • Include context if available

            💭 **All Ideas Captured** (don't miss any, even partial ones)
            • Idea 1: [Brief description]
            • Idea 2: [Brief description]
            • ...
            • Include even half-formed or interrupted ideas
            • Capture ideas even when people talk over each other

            🔍 **Idea Categories**
            Group similar ideas into 3-5 categories such as:
            
            **Category 1: [Name]**
            • Related idea 1
            • Related idea 2
            
            **Category 2: [Name]**
            • Related idea 3
            • Related idea 4

            💎 **Standout Concepts**
            • Most innovative ideas
            • Ideas that received positive reactions
            • Unique approaches mentioned

            🔄 **Potential Combinations**
            • Identify ideas that could be combined for greater impact
            • Note complementary concepts

            ⚡️ **Next Steps**
            • Suggested actions to develop promising ideas
            • Areas requiring further brainstorming
            • Potential prototypes or tests

            Important guidelines:
            - Capture ALL ideas, even those that seem incomplete or were interrupted
            - Don't filter out "bad ideas" - in brainstorming, all ideas have potential value
            - Pay attention to emotional reactions to ideas (excitement, agreement, etc.)
            - Note when ideas build upon each other
            - Preserve the creative essence of ideas even when they're expressed chaotically
            - Use simple language to describe complex ideas

            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 1200,
                "style": "comprehensive",
                "format": "structured",
                "preserve_all_ideas": True,
                "categorize_ideas": True
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

        "press_conference": {
            "system": "You are a news writer specialized in covering public events and press conferences.",
            "template": """
            Analyze this press conference and generate a structured news article:

            📰 **HEADLINE**
            • Brief, descriptive and attention-grabbing
            
            📌 **SUBHEADING**
            • Concise preview of the most relevant information

            📝 **LEAD PARAGRAPH**
            • Introductory paragraph that answers:
              - What happened
              - Who participated
              - Why it's important

            📄 **BODY OF THE ARTICLE**
            
            🔍 **Main Details**
            • Who: People/institutions involved
            • What: Central topic or announcement made
            • How: Method or form of implementation
            • When: Relevant dates and deadlines
            • Where: Location of the event/announcement
            • Why: Motivation or reason

            💬 **Notable Quotes**
            • Include relevant verbatim statements
            • Maintain the context of each quote

            ℹ️ **Additional Information**
            • Relevant background
            • Contextual data
            • Next steps

            Rules:
            - Maintain objective journalistic style
            - Prioritize factual information
            - Include relevant direct quotes
            - Omit unmentioned elements
            - Avoid speculation

            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "journalistic",
                "format": "news_article",
                "include_quotes": True
            }
        },

        "brainstorming": {
            "system": "You are an AI specialized in capturing and organizing ideas from brainstorming sessions where multiple people speak simultaneously and ideas flow rapidly without structure.",
            "template": """
            Analyze this brainstorming session and extract all valuable ideas, even those mentioned briefly or incompletely. Organize them in the following format:

            🌟 **Core Problem/Challenge**
            • Identify the central problem or challenge being addressed
            • Include context if available

            💭 **All Ideas Captured** (don't miss any, even partial ones)
            • Idea 1: [Brief description]
            • Idea 2: [Brief description]
            • ...
            • Include even half-formed or interrupted ideas
            • Capture ideas even when people talk over each other

            🔍 **Idea Categories**
            Group similar ideas into 3-5 categories such as:
            
            **Category 1: [Name]**
            • Related idea 1
            • Related idea 2
            
            **Category 2: [Name]**
            • Related idea 3
            • Related idea 4

            💎 **Standout Concepts**
            • Most innovative ideas
            • Ideas that received positive reactions
            • Unique approaches mentioned

            🔄 **Potential Combinations**
            • Identify ideas that could be combined for greater impact
            • Note complementary concepts

            ⚡️ **Next Steps**
            • Suggested actions to develop promising ideas
            • Areas requiring further brainstorming
            • Potential prototypes or tests

            Important guidelines:
            - Capture ALL ideas, even those that seem incomplete or were interrupted
            - Don't filter out "bad ideas" - in brainstorming, all ideas have potential value
            - Pay attention to emotional reactions to ideas (excitement, agreement, etc.)
            - Note when ideas build upon each other
            - Preserve the creative essence of ideas even when they're expressed chaotically
            - Use simple language to describe complex ideas

            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 1200,
                "style": "comprehensive",
                "format": "structured",
                "preserve_all_ideas": True,
                "categorize_ideas": True
            }
        },
        
        "global_summary": {
            "system": """Eres un asistente especializado en analizar conversaciones de Slack y generar resúmenes ejecutivos detallados. 
            Tu tarea es identificar temas importantes, patrones de comunicación, interdependencias entre canales y extraer información clave.""",
            "template": """
            Analiza las siguientes conversaciones de Slack que ocurrieron entre {start_date} y {end_date} en {channel_count} canales diferentes.
            
            Tu objetivo es crear un resumen global que:
            1. Identifique los temas principales discutidos en todos los canales
            2. Destaque las conversaciones más importantes y sus conclusiones
            3. Identifique patrones de comunicación entre canales (temas que aparecen en múltiples canales)
            4. Reconozca a los participantes clave y sus contribuciones principales
            5. Extraiga decisiones importantes y elementos de acción
            6. Identifique cualquier problema o desafío recurrente
            
            Organiza tu resumen en estas secciones:
            
            📊 **RESUMEN EJECUTIVO**
            • Una visión general concisa de toda la actividad
            • Tendencias principales observadas
            • Volumen y naturaleza de las comunicaciones
            
            🔍 **TEMAS PRINCIPALES**
            • Los temas más discutidos y su importancia
            • Cómo evolucionaron estos temas durante el período
            • Qué canales fueron más activos para cada tema
            
            ✅ **DECISIONES CLAVE**
            • Decisiones importantes tomadas durante este período
            • Quién tomó o influyó en cada decisión
            • Impacto potencial de estas decisiones
            
            📋 **ELEMENTOS DE ACCIÓN**
            • Tareas y responsabilidades asignadas
            • Plazos mencionados
            • Estado actual (si se puede determinar)
            
            ⚠️ **PROBLEMAS Y DESAFÍOS**
            • Problemas identificados que requieren atención
            • Bloqueos o impedimentos mencionados
            • Preocupaciones expresadas por los participantes
            
            👥 **PARTICIPANTES DESTACADOS**
            • Personas que tuvieron contribuciones significativas
            • Áreas de especialización o responsabilidad
            • Patrones de interacción entre participantes clave
            
            📢 **ANÁLISIS DE CANALES**
            • Breve resumen de la actividad en cada canal principal
            • Cómo se relacionan los canales entre sí
            • Canales más activos y su enfoque principal
            
            Usa un estilo ejecutivo, claro y conciso. Incluye ejemplos específicos cuando sea relevante, pero mantén el enfoque en las tendencias generales y la información más importante.
            
            Conversaciones a analizar:
            
            {text}
            """,
            "parameters": {
                "max_length": 2000,
                "style": "executive",
                "format": "structured"
            }
        },

        "auto": {
            "system": """You are an AI expert in content analysis and template selection.
            Your task is to analyze the given text and determine the most appropriate template
            for summarizing it based on its content, structure, and context.""",
            "parameters": {
                "max_length": 500,
                "style": "auto",
                "format": "structured"
            },
            "template": """
            Analyze this text and determine the most appropriate template to use for summarization.
            Consider these aspects:

            1. Content Type:
            - Is it a meeting? What kind? (1:1, team sync, presentation)
            - Is it a Slack conversation?
            - Is it a general document or transcript?
            - Is it a brainstorming session?

            2. Content Structure:
            - How formal/informal is it?
            - Is it structured or free-flowing?
            - Are there clear sections or topics?
            - Is it chaotic with multiple people speaking simultaneously?

            3. Content Elements:
            - Are there action items?
            - Are there decisions made?
            - Is there technical discussion?
            - Is there personal/career discussion?
            - Are there many ideas being generated rapidly?

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
            - press_conference: For press conferences and public announcements
            - brainstorming: For chaotic idea generation sessions with multiple speakers and rapid idea flow

            Text to analyze:
            {text}

            Respond with:
            template: [template_name]
            
            explanation:
            [Brief explanation of why this template is most appropriate]
            
            considerations:
            [Specific considerations for using this template]
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
