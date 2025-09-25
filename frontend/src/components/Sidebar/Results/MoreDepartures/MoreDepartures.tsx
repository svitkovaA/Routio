/**
 * @file MoreDepartures.tsx
 * @brief Displays a list of upcoming departures for the given public transport line from the given station
 * @author Andrea Svitkova (xsvitka00)
 */

import { Leg } from "../../../types/types";

type MoreDeparturesProps = {
    leg: Leg;
    recalculatePattern: (selectedIndex: number) => void;
}

function MoreDepartures({
    leg,
    recalculatePattern
} : MoreDeparturesProps) {
    return (
        <>
            {leg.otherOptions?.departures.map((departure, index) => (
                <div onClick={() => recalculatePattern(index)}>
                    {departure.departureTime}
                </div>
            ))}
        </>
    );
}
export default MoreDepartures;

/** End of file MoreDepartures.tsx */
