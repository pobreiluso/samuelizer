class MeetingMinutesError(Exception):
    """
    Base exception for the meeting minutes module.
    
    This class serves as the base for all specific exceptions
    in the meeting processing module.
    """
    pass

class TranscriptionError(MeetingMinutesError):
    """
    Error during the transcription process.
    
    Raised when there are problems converting audio to text,
    either due to issues with the OpenAI API or the audio file.
    """
    pass

class AnalysisError(MeetingMinutesError):
    """
    Error during content analysis.
    
    Raised when there are problems processing or analyzing the
    transcribed text, such as errors in summary generation or analysis.
    """
    pass

class DownloadError(MeetingMinutesError):
    """
    Error during video download.
    
    Raised when there are problems downloading videos from
    external sources like Google Drive or URLs.
    """
    pass

class AudioExtractionError(MeetingMinutesError):
    """
    Error during audio extraction.
    
    Raised when there are problems extracting audio from a
    video file or processing audio files.
    """
    pass
