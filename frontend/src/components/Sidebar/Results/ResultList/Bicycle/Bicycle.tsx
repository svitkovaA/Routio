/**
 * @file Bicycle.tsx
 * @brief Displays trip results for bicycle routes
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRoute, faStopwatch } from "@fortawesome/free-solid-svg-icons";
import Timeline from "../Timeline/Timeline";
import '../ResultListItem/ResultListItem.css';
import { useResult } from "../../../../ResultContext";

function Bicycle() {
    const {
        result,
        selectedTripPatternIndex, setSelectedTripPatternIndex
    } = useResult();

    return (
        <>
            {result.tripPatterns.map((pattern, index) => (
                <div 
                    className={"pattern " + (index === selectedTripPatternIndex ? "selected" : "")}
                    onClick={() => setSelectedTripPatternIndex(index)}
                >
                    <span className="time">
                        {new Date(pattern.legs[0]?.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <div className="pattern-content">
                        <Timeline 
                            totalDuration={pattern.totalDuration}
                            legs={pattern.legs}
                        />
                        <div className="grid-wrapper">
                            <span>
                                <FontAwesomeIcon icon={faStopwatch} />
                                {Math.round(pattern.totalDuration / 60)} min
                            </span>
                            <span>
                                <FontAwesomeIcon icon={faRoute} />
                                {(pattern.totalDistance / 1000).toFixed(1)} km
                            </span>
                        </div>
                    </div>
                    <span className="time">
                        {new Date(pattern.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                </div>
            ))}
        </>
    );
}

export default Bicycle;

/** End of file Bicycle.tsx */
