class FeatureDisabledException(Exception):
    def __init__(self, feature: str):
        self.feature = feature
        super().__init__(f"Feature {feature} is disabled")

class ResourceNotFoundException(Exception):
    def __init__(self, resource: str, resource_id: str):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} with id {resource_id} not found")

class ValidationException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
