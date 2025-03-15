"""
Configuración de proveedores de modelos de IA.
Este archivo permite configurar los diferentes proveedores y sus modelos.
"""

# Configuración de proveedores disponibles
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "description": "Servicios de IA de OpenAI (GPT, Whisper)",
        "env_var": "OPENAI_API_KEY",
        "transcription_models": ["whisper-1"],
        "analysis_models": [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-1106-preview"
        ],
        "default_transcription_model": "whisper-1",
        "default_analysis_model": "gpt-4"
    },
    "local": {
        "name": "Local Models",
        "description": "Modelos locales usando Whisper y Transformers",
        "env_var": None,  # No requiere API key
        "transcription_models": ["tiny", "base", "small", "medium", "large"],
        "analysis_models": [
            "facebook/bart-large-cnn", 
            "google/flan-t5-base", 
            "google/flan-t5-large"
        ],
        "default_transcription_model": "base",
        "default_analysis_model": "facebook/bart-large-cnn"
    }
}

def get_available_providers():
    """
    Obtiene la lista de proveedores disponibles
    
    Returns:
        dict: Diccionario con información de los proveedores
    """
    # Asegurarse de que el proveedor local esté registrado
    if "local" not in PROVIDERS:
        PROVIDERS["local"] = {
            "name": "Local Models",
            "description": "Modelos locales usando Whisper y Transformers",
            "env_var": None,  # No requiere API key
            "transcription_models": ["tiny", "base", "small", "medium", "large"],
            "analysis_models": [
                "facebook/bart-large-cnn", 
                "google/flan-t5-base", 
                "google/flan-t5-large"
            ],
            "default_transcription_model": "base",
            "default_analysis_model": "facebook/bart-large-cnn"
        }
    return PROVIDERS

def get_provider_config(provider_name):
    """
    Obtiene la configuración de un proveedor específico
    
    Args:
        provider_name: Nombre del proveedor
        
    Returns:
        dict: Configuración del proveedor o None si no existe
    """
    return PROVIDERS.get(provider_name.lower())

def get_provider_models(provider_name, model_type="transcription"):
    """
    Obtiene los modelos disponibles para un proveedor y tipo específicos
    
    Args:
        provider_name: Nombre del proveedor
        model_type: Tipo de modelo (transcription o analysis)
        
    Returns:
        list: Lista de modelos disponibles
    """
    provider = get_provider_config(provider_name)
    if not provider:
        return []
        
    if model_type == "transcription":
        return provider.get("transcription_models", [])
    elif model_type == "analysis":
        return provider.get("analysis_models", [])
    return []

def get_default_model(provider_name, model_type="transcription"):
    """
    Obtiene el modelo predeterminado para un proveedor y tipo específicos
    
    Args:
        provider_name: Nombre del proveedor
        model_type: Tipo de modelo (transcription o analysis)
        
    Returns:
        str: Modelo predeterminado o None si no existe
    """
    provider = get_provider_config(provider_name)
    if not provider:
        return None
        
    if model_type == "transcription":
        return provider.get("default_transcription_model")
    elif model_type == "analysis":
        return provider.get("default_analysis_model")
    return None
