
from dataclasses import asdict, dataclass, field
from enum import Enum

class RunState (str, Enum):
    DRAFT =  "DRAFT"
    ANALYZING = "ANALYZING"
    REVIEW_READY = "REVIEW_READY"
    BOOTSTRAPPING = "BOOTSTRAPPING"
    CI_RUNNING = "CI_RUNNING"
    DEPLOYING = "DEPLOYING"
    VALIDATING = "VALIDATING"
    LIVE = "LIVE"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"
    DESTROYED = "DESTROYED"

ALLOWED_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.DRAFT: {
        RunState.ANALYZING,
    },

    RunState.ANALYZING: {
        RunState.REVIEW_READY,
        RunState.FAILED,
        RunState.CANCELLED,
    },

    RunState.REVIEW_READY: {
        RunState.BOOTSTRAPPING,
        RunState.FAILED,
        RunState.CANCELLED,
        RunState.DESTROYED,
    },

    RunState.BOOTSTRAPPING: {
        RunState.CI_RUNNING,
        RunState.FAILED,
        RunState.ROLLED_BACK,
        RunState.CANCELLED,
    },

    RunState.CI_RUNNING: {                
        RunState.DEPLOYING,
        RunState.VALIDATING,
        RunState.FAILED,
        RunState.ROLLED_BACK,                
        RunState.CANCELLED,
    },

    RunState.DEPLOYING: {
        RunState.VALIDATING,
        RunState.FAILED,
        RunState.CANCELLED,
        RunState.ROLLED_BACK,
    },

    RunState.VALIDATING: {
        RunState.LIVE,
        RunState.FAILED,
        RunState.ROLLED_BACK,
        RunState.CANCELLED,
    },

    RunState.LIVE: {
        RunState.DEPLOYING,
        RunState.FAILED,
        RunState.ROLLED_BACK,
        RunState.DESTROYED,
    },

    RunState.FAILED: {
        RunState.ANALYZING,
        RunState.BOOTSTRAPPING,
        RunState.ROLLED_BACK,
        RunState.DESTROYED,
    },

    RunState.ROLLED_BACK: {
        RunState.BOOTSTRAPPING,
        RunState.DESTROYED,
    },

    RunState.CANCELLED: {
        RunState.BOOTSTRAPPING,
        RunState.DESTROYED,
    },

    RunState.DESTROYED: set(),

}
 
def transition(current: RunState, target: RunState)-> RunState:
    if target == current:
        return current

    allowed_targets = ALLOWED_TRANSITIONS.get(current, set())

    if target not in allowed_targets:
        raise ValueError(
            f"Invalid deployment state transition: "
            f"{current.value} -> {target.value}"
        )
    return target

@dataclass
class ServiceSpec:
    name: str
    root: str
    framework: str
    version: str
    package_manager: str
    install_command: str
    build_command: str
    start_command: str
    port: int = 3000
    scripts: dict[str, str] = field(default_factory=dict)

@dataclass
class ProjectSpec:
    name: str
    source_path: str
    services: list[ServiceSpec]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)