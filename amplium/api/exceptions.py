"""Class for Amplium exceptions"""


class AmpliumException(RuntimeError):
    """Thrown if there is no available capacity for new sessions"""
    def __init__(self, message, error, status_code):
        super().__init__(message)

        self.error = error
        self.status_code = status_code


class NoAvailableCapacityException(AmpliumException):
    """Thrown if there is no available capacity for new sessions"""
    def __init__(self, message=""):
        super().__init__(message, "AMPLIUM_NO_AVAILABLE_CAPACITY", 429)


class NoAvailableGridsException(AmpliumException):
    """Thrown if there are no grids registered to Amplium"""
    def __init__(self, message=""):
        super().__init__(message, "AMPLIUM_NO_AVAILABLE_GRIDS", 429)


class IntegrationNotConfigured(AmpliumException):
    """Thrown if we try to use an integration and it is not configured correctly"""
    def __init__(self, message=""):
        super().__init__(message, "AMPLIUM_INTEGRATION_NOT_CONFIGURED", 500)
