/**
 * @file MoreDepartures.tsx
 * @brief Displays alternative departures for a public transport leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { Leg } from "../../../types/types";
import { timelineIcons } from "../../Planning/Icons/Icons";
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import "./MoreDepartures.css"

type MoreDeparturesProps = {
    leg: Leg;                                               // Public transport leg for which alternative departures are displayed
    recalculatePattern: (selectedIndex: number) => void;    // Callback triggering route recalculation for a selected departure
}

function MoreDepartures({
    leg,
    recalculatePattern
} : MoreDeparturesProps) {
    return (
        <div className="more-departure-detail">
            {leg?.otherOptions?.departures.map((departure, index) => {   
                const currentIndex = leg?.otherOptions?.currentIndex; 

                return (
                    <div
                        key={`${index}`}
                        className={"more-departure-row" + (currentIndex === index ? " selected" : "") + (currentIndex === index + 1 ? " before-selected" : "")}
                        onClick={() => recalculatePattern(index)}
                    >   
                        <div className="more-departure-left">
                                {timelineIcons[leg.mode]}

                                <span
                                    className="detail-public-code"
                                    style={{ backgroundColor: leg.color }}
                                >
                                    {leg.line?.publicCode}
                                </span>

                                <span>
                                    <ArrowForwardIcon sx={{ fontSize: 16 }} />
                                </span>

                                <span className="direction">
                                    {departure.direction}
                                </span>
                        </div>
                        <div className="more-departure-right">
                            <span>
                                {new Date(departure.departureTime).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit",})}
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
export default MoreDepartures;

/** End of file MoreDepartures.tsx */
