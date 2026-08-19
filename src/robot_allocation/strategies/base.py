"""Common interface for single-client, single-pool allocation strategies."""
# ABC + abstractmethod let us define a formal interface: any subclass that
# doesn't implement `allocate` cannot be instantiated.
from abc import ABC, abstractmethod

from ..domain.allocation_result import AllocationResult
from ..domain.inventory import RobotInventory


class AllocationStrategy(ABC):
    """Implemented by Level 1 (category distribution) and Level 2
    (cost-optimised). Level 3 and Level 4 have an extra standby-pool
    parameter and so intentionally don't share this exact signature --
    see :mod:`standby_activation_strategy` and :mod:`multi_client_strategy`.
    """

    @abstractmethod
    def allocate(self, inventory: RobotInventory, requested_hours: int) -> AllocationResult:
        # No implementation here -- subclasses (CategoryDistributionStrategy,
        # CostOptimizedStrategy) must provide their own `allocate` method.
        # `inventory` is the pool of robots available; `requested_hours` is
        # how many hours of work the client needs covered.
        ...
