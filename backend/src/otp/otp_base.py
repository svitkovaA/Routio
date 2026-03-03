"""
file: otp_base.py

Base class for all OpenTripPlanner clients.
"""

from abc import ABC
from typing import Any, Callable, Dict, TypeVar, final
from gql import GraphQLRequest
from routing_engine.routing_context import RoutingContext

# Generic return type for parsed OTP responses
T = TypeVar("T")

class OTPBase(ABC):
    """
    Abstract base class for OTP GraphQL clients.
    """
    def __init__(self, context: RoutingContext):
        """
        Initializes OTP base client.

        Args:
            context: Global routing context
        """
        self._ctx = context

    @final
    async def _execute_query(
        self,
        query: GraphQLRequest,
        variables: Dict[str, Any],
        parser: Callable[[Any], T],
        fallback: T
    ) -> T:
        """
        Executes a GraphQL query and parses the response.

        Args:
            query: GraphQLRequest object representing the query
            variables: Dictionary of query variables
            parser: Callable responsible for converting raw GraphQL response
            fallback: Value returned if query execution fails

        Returns:
            Parsed response of type T
        """
        try:
            # Execute GraphQL query
            result = await self._ctx.session.execute(query, variable_values=variables)

            # Parse raw response
            return parser(result)

        except Exception as e:
            print(e)
            # Return fallback value on failure
            return fallback

# End of file otp_base.py
