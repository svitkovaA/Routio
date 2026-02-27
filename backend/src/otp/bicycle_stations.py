from typing import Dict, List
from gql import gql
from otp.otp_base import OTPBase
from models.route import BikeStationNodeWrapper

class OTPBicycleStations(OTPBase):
    QUERY = gql("""
        query nearestStations($latitude: Float!, $longitude: Float!, $maximum_distance: Float!) {
            nearest(
                latitude: $latitude,
                longitude: $longitude,
                maximumDistance: $maximum_distance,
                filterByPlaceTypes: [bicycleRent]
            ) {
                edges {
                    node {
                        distance
                        place {
                            latitude
                            longitude
                            ... on BikeRentalStation {
                                id
                                name
                                bikesAvailable
                                spacesAvailable
                                allowDropoff
                            }
                        }
                    }
                }
            }
        }
    """)

    async def execute(
        self,
        latitude: float,
        longitude: float,
        maximum_distance: float
    ) -> List[BikeStationNodeWrapper]:
        variables: Dict[str, float] = {
            "latitude": latitude,
            "longitude": longitude,
            "maximum_distance": maximum_distance
        }

        return await self._execute_query(
            self.QUERY,
            variables,
            lambda r: [
                BikeStationNodeWrapper.model_validate(node)
                for node in r["nearest"]["edges"]
            ],
            fallback=[]
        )
