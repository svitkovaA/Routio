from abc import ABC
from typing import Any, Callable, Dict, TypeVar, final
from gql import GraphQLRequest
from routing_engine.routing_context import RoutingContext

T = TypeVar("T")

class OTPBase(ABC):
    def __init__(self, context: RoutingContext):
        self._ctx = context

    @final
    async def _execute_query(
        self,
        query: GraphQLRequest,
        variables: Dict[str, Any],
        parser: Callable[[Any], T],
        fallback: T
    ) -> T:
        try:
            # Execute GraphQL query
            result = await self._ctx.session.execute(query, variable_values=variables)

            # Parse result using provided parser
            return parser(result)

        except Exception:
            # Return fallback value on failure
            return fallback
