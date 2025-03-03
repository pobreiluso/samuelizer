# Samuelizer

**Samuelizer** es una herramienta de inteligencia artificial diseñada para resumir de manera automática conversaciones de Slack, reuniones, transcripciones de audio/video y otros contenidos relacionados. Aprovecha tecnologías de vanguardia (como los modelos de OpenAI) para transformar larga información en resúmenes claros, concisos y visualmente atractivos, facilitando la toma de decisiones y el análisis rápido de la información.

---

## Tabla de Contenidos

- [Características Principales](#caracter%C3%ADsticas-principales)
- [Instalación y Requerimientos](#instalaci%C3%B3n-y-requerimientos)
- [Uso y Ejemplos](#uso-y-ejemplos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Contribuciones](#contribuciones)
- [Mantenimiento y Roadmap](#mantenimiento-y-roadmap)
- [Licencia](#licencia)
- [Autores y Contacto](#autores-y-contacto)

---

## Características Principales

- **Análisis de Slack:**  
  - Descarga y procesado de mensajes de Slack (canal o hilo).  
  - Reemplazo inteligente de menciones de usuario para una mejor legibilidad.  
  - Filtros por rango de fechas.

- **Transcripción de Audio/Video:**  
  - Extracción y optimización de audio desde múltiples formatos (MP4, AVI, MKV, MP3, WAV, etc.).  
  - Transcripción automática mediante el modelo *Whisper* de OpenAI.

- **Generación de Resúmenes:**  
  - Resumen ejecutivo, análisis de sentimientos, puntos clave, y acciones a seguir.
  - **Selección Automática de Plantillas:** La IA analiza el contenido y selecciona automáticamente la plantilla óptima según el contexto.
  - Personalización de plantillas de análisis (ej. resumen, ejecutivo, rápido, etc.)  
  - Procesamiento y segmentación de textos largos para cumplir con las limitaciones de tokens.

- **Documentación Automatizada:**  
  - Exportación de resúmenes y análisis a documentos DOCX.
  - Uso de Markdown para mejorar la presentación de la información.

- **Interfaz de Línea de Comando (CLI):**  
  - Comandos claros para cada modalidad: análisis de medios, texto, Slack, grabación en tiempo real, etc.
  - Comando `version` para consultar la versión actual del agente.

- **Integración y Automatización:**  
  - Uso de Poetry para la gestión de dependencias y scripts.
  - Makefile con targets para instalación, test, lint, formateo, documentación y ejecución del proyecto.

---

## Instalación y Requerimientos

### Requisitos Previos

- **Sistema Operativo:**  
  - Compatible con Windows, macOS y Linux.
- **Python:**  
  - Versión 3.12 o superior.
- **Poetry:**  
  - Para la gestión de entornos y dependencias.
  
  Puedes instalar Poetry mediante:
  ```bash
  # macOS / Linux
  curl -sSL https://install.python-poetry.org | python3 -
  
  # Windows PowerShell
  (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
  ```

### Pasos de Instalación

1. **Clonar el Repositorio:**
   ```bash
   git clone https://github.com/tu_usuario/samuelizer.git
   cd samuelizer
   ```

2. **Instalar las Dependencias:**
   ```bash
   poetry install
   ```

3. **Configurar el Entorno:**
   - Renombra el archivo `.env.example` a `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edita el archivo `.env` para incluir tus credenciales y configuraciones, por ejemplo:
     ```env
     OPENAI_API_KEY=tu_openai_api_key
     SLACK_TOKEN=tu_slack_token
     SLACK_RATE_LIMIT_DELAY=1.0
     SLACK_BATCH_SIZE=1000
     OUTPUT_DIR=slack_exports
     LOG_FILE=slack_download.log
     ```

4. **Verificar la Instalación:**
   - Ejecuta:
     ```bash
     poetry run samuelize version
     ```
   - Debe mostrarte la versión actual del agente.

---

## Uso y Ejemplos

La aplicación cuenta con múltiples comandos de CLI que permiten acceder a distintas funcionalidades. A continuación, algunos ejemplos de uso:

### Análisis de Medios (Audio/Video)
```bash
poetry run samuelize media ruta/al/archivo.mp4 --api_key tu_openai_api_key --optimize 32k --template executive
```

### Resumen de Texto
```bash
poetry run samuelize text "Texto a analizar" --template quick
```

### Análisis de Mensajes Slack
```bash
poetry run samuelize slack CHANNEL_ID --start-date 2024-01-01 --end-date 2024-02-01
```

### Grabación y Análisis en Tiempo Real
```bash
poetry run samuelize listen --duration 300
```
*Nota:* Si no se especifica duración, la grabación será continua hasta interrumpirla manualmente (Ctrl+C).

### Consultar la Versión
```bash
poetry run samuelize version
```

---

## Estructura del Proyecto

El repositorio tiene la siguiente organización principal:

- **src/**: Contiene el código fuente.
  - **cli.py**: Punto de entrada de la aplicación CLI.
  - **transcription/**: Módulo de transcripción y resúmenes, con plantillas y manejo de excepciones.
  - **slack/**: Integración con la API de Slack para descargar y procesar mensajes.
  - **audio_capture/**: Código para la captura y procesamiento del audio del sistema.
  - **config/**: Configuración global y manejo de variables de entorno.
  - **utils/**: Utilidades varias (extracción de audio, helpers, etc.).

- **Makefile**: Automación de tareas comunes (setup, test, lint, docs, etc.).
- **pyproject.toml**: Configuración del proyecto y las dependencias gestionadas con Poetry.
- **.env**: Archivo de configuración para claves y parámetros sensibles.
- **README.md**: Este archivo, el cual explica a detalle el uso y las características del proyecto.

---

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas colaborar:

1. **Fork del Repositorio:**  
   Realiza un *fork* y crea una rama para tu funcionalidad o corrección.
2. **Crear Pull Request:**  
   Envía tus cambios con una descripción clara del aporte.
3. **Issues y Feedback:**  
   Abre un issue para reportar errores, proponer mejoras o discutir nuevas funcionalidades.

Por favor, sigue la [Guía de Contribución](CONTRIBUTING.md) del proyecto y respeta las normas de estilo de código.

---

## Mantenimiento y Roadmap

### Roadmap (Planes Futuros)

- **Optimización de Plantillas:**  
  Implementación de un motor de plantillas (por ejemplo, Jinja2) para mayor flexibilidad y reusabilidad.
- **Mejoras en el Procesamiento de Audio:**  
  Incorporar manejo avanzado de errores y optimización en la extracción de audio.
- **Integración Continua:**  
  Implementar pipelines de CI/CD para tests automáticos, análisis de estilo y despliegues.
- **Interfaz Web:**  
  Exploración de una interfaz gráfica web para facilitar el uso por parte de usuarios no expertos.
- **Soporte Multilenguaje:**  
  Ampliar el sistema de plantillas a otros idiomas y contextos.

---

## Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE). Se eligió la Licencia MIT por su simplicidad y flexibilidad, permitiendo a otros desarrolladores utilizar, modificar y distribuir el código de manera libre.

---

## Autores y Contacto

- **ajerez** –  
  Correo: [pobreiluso@gmail.com](mailto:pobreiluso@gmail.com)  
  [GitHub](https://github.com/ajerez) | [Linkedin](https://www.linkedin.com/in/ajerez/)

Si tienes dudas, sugerencias o deseas colaborar adicionalmente, no dudes en ponerte en contacto.

---

Este README está diseñado para servir tanto a desarrolladores como a usuarios finales, facilitando la comprensión, instalación y uso del proyecto sin importar su nivel de experiencia. ¡Bienvenido a Samuelizer!

