from enum import Enum

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELETED = "deleted"