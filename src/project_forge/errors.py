"""Domain errors shared by Project Forge services."""


class ProjectForgeError(Exception):
    """Base error for user-actionable Project Forge failures."""


class ContractError(ProjectForgeError):
    """Raised when a Project Forge contract is invalid or unsupported."""


class ExecutionBlocked(ProjectForgeError):
    """Raised when command execution violates the safety policy."""
