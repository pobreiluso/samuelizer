class MeetingMinutesError(Exception):
    """
    Excepción base para el módulo de actas de reuniones.
    
    Esta clase sirve como base para todas las excepciones específicas
    del módulo de procesamiento de reuniones.
    """
    pass

class TranscriptionError(MeetingMinutesError):
    """
    Error durante el proceso de transcripción.
    
    Se lanza cuando hay problemas al convertir audio a texto,
    ya sea por problemas con la API de OpenAI o el archivo de audio.
    """
    pass

class AnalysisError(MeetingMinutesError):
    """
    Error durante el análisis del contenido.
    
    Se lanza cuando hay problemas al procesar o analizar el texto
    transcrito, como errores en la generación de resúmenes o análisis.
    """
    pass

class DownloadError(MeetingMinutesError):
    """
    Error durante la descarga de video.
    
    Se lanza cuando hay problemas al descargar videos desde
    fuentes externas como Google Drive o URLs.
    """
    pass

class AudioExtractionError(MeetingMinutesError):
    """
    Error durante la extracción de audio.
    
    Se lanza cuando hay problemas al extraer el audio de un
    archivo de video o al procesar archivos de audio.
    """
    pass
