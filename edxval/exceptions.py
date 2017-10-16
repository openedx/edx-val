"""
VAL Exceptions.
"""

class ValError(Exception):
    """
    An error that occurs during VAL actions.

    This error is raised when the VAL API cannot perform a requested
    action.

    """
    pass


class ValInternalError(ValError):
    """
    An error internal to the VAL API has occurred.

    This error is raised when an error occurs that is not caused by incorrect
    use of the API, but rather internal implementation of the underlying
    services.

    """
    pass


class ValVideoNotFoundError(ValError):
    """
    This error is raised when a video is not found

    If a state is specified in a call to the API that results in no matching
    entry in database, this error may be raised.

    """
    pass


class ValCannotCreateError(ValError):
    """
    This error is raised when an object cannot be created
    """
    pass


class ValCannotUpdateError(ValError):
    """
    This error is raised when an object cannot be updated
    """
    pass


class InvalidTranscriptFormat(ValError):
    """
    This error is raised when an transcript format is not supported
    """
    pass


class InvalidTranscriptProvider(ValError):
    """
    This error is raised when an transcript provider is not supported
    """
    pass
