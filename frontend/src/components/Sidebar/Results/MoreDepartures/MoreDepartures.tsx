/**
 * @file MoreDepartures.tsx
 * @brief Displays alternative departures for a public transport leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { Leg } from "../../../types/types";

type MoreDeparturesProps = {
    leg: Leg;                                               // Public transport leg for which alternative departures are displayed
    recalculatePattern: (selectedIndex: number) => void;    // Callback triggering route recalculation for a selected departure
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
