class MeetingMinutesError(Exception):
    """Base exception for meeting minutes module"""
    pass

class TranscriptionError(MeetingMinutesError):
    """Raised when transcription fails"""
    pass

class AnalysisError(MeetingMinutesError):
    """Raised when analysis fails"""
    pass

class DownloadError(MeetingMinutesError):
    """Raised when video download fails"""
    pass

class AudioExtractionError(MeetingMinutesError):
    """Raised when audio extraction fails"""
    pass
