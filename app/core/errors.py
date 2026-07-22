class BaseDomainError(Exception):
    pass

# ===== NOT EXISTS =====
class EntityError(BaseDomainError):
    pass

class ProposalNotFoundError(EntityError):
    pass

class UserNotFoundError(EntityError):
    pass

class VoteNotFoundError(EntityError):
    pass

# ===== NO RIGHTS =====
class PermissionError(BaseDomainError):
    pass

class NotParticipantError(PermissionError):
    pass

class NotAuthorError(PermissionError):
    pass

# ===== WRONG STATE =====
class LifecycleError(BaseDomainError):
    pass

class InvalidProposalStatusError(LifecycleError):
    pass

# ===== BAD DATA =====
class ValidationError(BaseDomainError):
    pass

class InvalidVoteValueError(ValidationError):
    pass

class EmptyParticipantsError(ValidationError):
    pass

class DuplicateParticipantsError(ValidationError):
    pass

# ===== BREAKING RULES =====
class BusinessRuleError(BaseDomainError):
    pass

class AlreadyVotedError(BusinessRuleError):
    pass