from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class PromptTemplates:
    DEFAULT_TEMPLATES = {
        "summary": {
            "system": "You are an AI specialized in creating concise, factual summaries that capture the essence of content.",
            "template": """
            Create a concise summary of the following text:
            
            • Focus on the main topic and key information
            • Use clear, direct language
            • Maintain a neutral, factual tone
            • Avoid redundancy and unnecessary details
            • Organize information logically
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 400,
                "style": "concise",
                "format": "paragraph"
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
            "system": "You are an AI specialized in creating balanced, comprehensive summaries that capture the essence of any content type.",
            "template": """
            Analyze the following text and generate a structured summary that captures the most relevant information:

            📝 **Main Topic**
            • Identify the central topic or purpose
            • Provide essential context
            
            💡 **Key Information**
            • Extract the most important information
            • Focus on facts, not opinions
            • Prioritize unique and valuable insights
            
            ✅ **Outcomes**
            • Identify conclusions, decisions, or results
            • Include action items only if explicitly mentioned
            
            Use markdown format for better readability.
            Be concise but comprehensive.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 600,
                "style": "balanced",
                "format": "structured"
            }
        },

        "executive": {
            "system": "You are an AI specialized in creating executive summaries focused on decisions and business impact.",
            "template": """
            Generate a structured executive summary:

            🎯 **Purpose & Context**
            • Main objective or background (1-2 sentences)
            
            💡 **Key Insights**
            • 2-3 most important insights
            • Focus on business relevance
            
            ✨ **Decisions & Outcomes**
            • Concrete decisions made
            • Expected impact of each decision
            
            📋 **Action Plan**
            • Critical next steps
            • Responsibilities and deadlines
            
            Use professional, direct language.
            Prioritize actionable information.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 600,
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
            "system": "You are an AI specialized in extracting essential information from Slack conversations.",
            "template": """
            Extract only the essential information from this Slack conversation:

            📍 **Topic**
            • The main subject in one sentence
            
            ✅ **Decisions**
            • Only final decisions made
            • No discussion context
            
            ⚡️ **Actions**
            • Only concrete tasks assigned
            • Include who is responsible
            
            Use extreme brevity.
            Include only critical information.
            Preserve @mentions and #channels.
            
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
            "system": "You are an AI specialized in analyzing 1:1 meetings with focus on personal development and career growth.",
            "template": """
            Analyze this 1:1 meeting and provide a structured summary:

            🚦 **Current Challenges**
            • Personal and professional blockers
            • Areas where support is needed
            
            💡 **Growth & Development**
            • Career aspirations discussed
            • Skills development and learning opportunities
            • Feedback received or given
            
            🎯 **Performance & Goals**
            • Progress on personal objectives
            • Achievements and recognition
            • Areas for improvement
            
            ⚡️ **Personal Action Items**
            • Specific commitments made
            • Resources or support requested
            • Follow-up items
            
            Use markdown format for better readability.
            Focus on the individual's perspective and needs.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 700,
                "style": "supportive",
                "format": "structured",
                "include_action_items": True
            }
        },

        "brainstorming": {
            "system": "You are an AI specialized in capturing and organizing ideas from creative brainstorming sessions.",
            "template": """
            Analyze this brainstorming session and extract all valuable ideas:

            🎯 **Challenge/Opportunity**
            • The central problem or opportunity being addressed
            
            💭 **Ideas Generated**
            • Capture ALL ideas mentioned, even briefly
            • Include partial or undeveloped concepts
            • Preserve the creative intent of each idea
            
            🔍 **Idea Categories**
            • Group similar ideas into 3-5 logical categories
            • Name each category to reflect its theme
            • List related ideas under each category
            
            💎 **Promising Concepts**
            • Identify ideas that received positive reactions
            • Note ideas with potential for immediate implementation
            • Highlight particularly innovative approaches
            
            🔄 **Synthesis Opportunities**
            • Identify complementary ideas that could be combined
            • Note potential evolution paths for promising ideas
            
            Use markdown format for better readability.
            Focus on capturing the creative essence without judgment.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 1000,
                "style": "creative",
                "format": "structured",
                "preserve_all_ideas": True,
                "categorize_ideas": True
            }
        },

        "weekly_sync": {
            "system": "You are an AI specialized in analyzing team progress meetings with focus on project advancement and coordination.",
            "template": """
            Analyze this team sync meeting and provide a structured summary:

            📊 **Progress Overview**
            • Key accomplishments since last meeting
            • Status of ongoing initiatives
            • Metrics and results mentioned
            
            🚧 **Challenges & Blockers**
            • Current obstacles
            • Resource constraints
            • Dependencies requiring attention
            
            🔄 **Coordination Points**
            • Cross-team dependencies
            • Handoffs and collaborations
            • Communication needs
            
            📅 **Next Period Plan**
            • Priorities for the coming week/sprint
            • Upcoming deadlines and milestones
            • Resource allocation decisions
            
            ⚡️ **Team Action Items**
            • Specific tasks with owners
            • Decisions requiring implementation
            • Follow-up commitments
            
            Use markdown format for better readability.
            Focus on team coordination and project advancement.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 800,
                "style": "practical",
                "format": "structured",
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

        "technical_meeting": {
            "system": "You are an AI specialized in analyzing technical discussions with focus on architecture, implementation, and technical decisions.",
            "template": """
            Analyze this technical meeting and provide a structured summary:

            🔍 **Technical Context**
            • Systems/components under discussion
            • Current state and constraints
            • Technical objectives
            
            🛠️ **Technical Challenges**
            • Problems identified
            • Technical limitations
            • Performance or scalability concerns
            
            💻 **Solution Approaches**
            • Proposed technical solutions
            • Architecture decisions
            • Implementation strategies
            • Trade-offs discussed
            
            📊 **Technical Criteria**
            • Success metrics mentioned
            • Non-functional requirements
            • Testing and validation approaches
            
            ⚡️ **Technical Action Items**
            • Implementation tasks
            • Research or investigation needed
            • Technical decisions pending
            
            Use markdown format with `code` for technical terms.
            Focus on technical details and engineering decisions.
            
            Text to analyze:
            {text}
            """,
            "parameters": {
                "max_length": 900,
                "style": "technical",
                "format": "structured",
                "include_code_references": True,
                "include_action_items": True
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
            - Is it a meeting? What kind? (1:1, team sync, technical discussion)
            - Is it a Slack conversation?
            - Is it a brainstorming session with multiple ideas?
            - Is it a formal presentation or announcement?

            2. Content Structure:
            - How formal/informal is it?
            - Is it structured or free-flowing?
            - Are there clear sections or topics?
            - Is it chaotic with multiple people speaking?

            3. Content Focus:
            - Is it focused on personal development? (one_to_one)
            - Is it focused on team progress? (weekly_sync)
            - Is it focused on technical details? (technical_meeting)
            - Is it focused on generating ideas? (brainstorming)
            - Is it a brief exchange needing minimal context? (slack_brief)
            - Is it a formal announcement? (press_conference)
            - Is it a general discussion? (summary or default)

            Available templates:
            - one_to_one: For 1:1 meetings with focus on personal/career development
            - weekly_sync: For team status updates and planning
            - executive: For formal meetings with business decisions
            - technical_meeting: For technical discussions and architecture
            - brainstorming: For idea generation sessions
            - slack_brief: For Slack conversations needing minimal context
            - slack_detailed: For complex Slack discussions
            - summary: For general content requiring standard summary
            - default: For general content when no specific template fits

            Text to analyze:
            {text}

            Respond with:
            template: [template_name]
            
            explanation:
            [Brief explanation of why this template is most appropriate]
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
            logger.warning(f"Template '{template_name}' no encontrado. Usando template 'default'.")
            template_name = "default"
            
        # Crear una clave de caché basada en el nombre del template y los parámetros
        cache_key = f"{template_name}_{hash(frozenset(kwargs.items()))}"
        
        # Verificar si el template ya está en caché
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
            
        template = self.templates[template_name].copy()
        
        # Crear una copia profunda de los parámetros para evitar modificar el original
        template["parameters"] = template["parameters"].copy()
        
        # Actualizar parámetros con los proporcionados
        template["parameters"].update(kwargs)
        
        # Guardar en caché
        self._template_cache[cache_key] = template
        
        return template
        
    def get_template_names(self) -> List[str]:
        """Obtiene la lista de nombres de templates disponibles"""
        return list(self.templates.keys())

    def add_custom_template(self, name: str, template: dict):
        """Añade un nuevo template personalizado"""
        required_keys = {"system", "template", "parameters"}
        if not all(key in template for key in required_keys):
            raise ValueError(f"El template debe contener: {required_keys}")
            
        self._custom_templates[name] = template
        self._templates[name] = template
        
        # Limpiar caché cuando se añade un nuevo template
        self._template_cache = {}
        
        return True

    def modify_template(self, name: str, modifications: dict):
        """Modifica un template existente"""
        if name not in self._templates:
            raise ValueError(f"Template '{name}' no encontrado")
            
        # Crear una copia del template para evitar modificar el original
        template = self._templates[name].copy()
        
        # Aplicar modificaciones
        for key, value in modifications.items():
            if key in template:
                if isinstance(template[key], dict) and isinstance(value, dict):
                    # Crear una copia del diccionario para evitar modificar el original
                    template[key] = template[key].copy()
                    template[key].update(value)
                else:
                    template[key] = value
        
        # Actualizar el template
        self._templates[name] = template
        
        # Si es un template personalizado, actualizar también en custom_templates
        if name in self._custom_templates:
            self._custom_templates[name] = template
            
        # Limpiar caché cuando se modifica un template
        self._template_cache = {}
        
        return True
        
    def optimize_template_for_length(self, template_name: str, text_length: int, max_allowed_length: int = 15000) -> dict:
        """
        Optimiza un template para manejar textos largos
        
        Args:
            template_name: Nombre del template a optimizar
            text_length: Longitud del texto a analizar
            max_allowed_length: Longitud máxima permitida para el modelo
            
        Returns:
            dict: Template optimizado
        """
        template = self.get_template(template_name)
        
        # Si el texto es demasiado largo, ajustar el template
        if text_length > max_allowed_length:
            # Calcular el factor de reducción
            reduction_factor = max_allowed_length / text_length
            
            # Crear un template optimizado para textos largos
            template["system"] = f"{template['system']} You are analyzing a truncated text that represents {int(reduction_factor*100)}% of the original content."
            
            # Modificar el template para indicar estrategias de manejo de texto largo
            original_template = template["template"]
            template["template"] = f"""
            NOTA: El texto original era demasiado largo ({text_length} caracteres) y ha sido truncado para su análisis.
            
            Estrategias para analizar este texto truncado:
            1. Enfócate en las secciones disponibles sin hacer suposiciones sobre el contenido faltante
            2. Prioriza la información más relevante y accionable
            3. Sé conciso y directo en tu análisis
            4. Indica claramente si detectas que falta información crítica
            
            {original_template}
            """
            
            # Ajustar parámetros para textos largos
            template["parameters"]["max_length"] = min(template["parameters"].get("max_length", 800), 500)
            template["parameters"]["style"] = "concise"
            
        return template
