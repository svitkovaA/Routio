/**
 * @file PublicTransportDetail.tsx
 * @brief Displays the detail section for a public transport leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleDown, faRoute, faStopwatch } from "@fortawesome/free-solid-svg-icons";
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import DepartureBoardIcon from '@mui/icons-material/DepartureBoard';
import { Leg, VerticalTimeline } from "../../../../types/types";
import "./PublicTransportDetail.css";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";

type PublicTransportDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
    moreDeparturesClick: () => void;
    recalculatePattern: (selectedIndex: number) => void;
}

function PublicTransportDetail({
    leg,
    setVerticalTimeline,
    index,
    moreDeparturesClick,
    recalculatePattern
} : PublicTransportDetailProps) {
    const [stopsOpen, setStopsOpen] = useState<boolean>(false);
    const [departuresOpen, setDeparturesOpen] = useState<boolean>(false);
    const publicTransportDetailRef = useRef<HTMLDivElement>(null);

    const averageDelay = () => {
        if (!leg.delays) return null;

        const values = Object.values(leg.delays);
        if (values.length === 0) return null;

        const total = values.reduce((sum, v) => sum + v, 0);
        return Math.round(total / values.length);
    }

    const averageDelayValue = averageDelay();

    useVerticalTimeLineHandle(
        publicTransportDetailRef,
        leg,
        setVerticalTimeline,
        index,
        -33
    );


    return (
        <div
            ref={publicTransportDetailRef} className="public-transport-detail"
        >
            <div className="waystop">
                {new Date(leg.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} {leg.fromPlace?.name}
            </div>
            {leg.mode + " " + leg.line?.publicCode + " -> " + leg.serviceJourney?.direction}
            <div>
                {leg.nonContinuousDepartures ? (
                    <div className="non-continuous-departures">
                        <span className="exclamation">
                            <PriorityHighIcon />
                        </span>
                        No more available times for this {leg.mode}. Reroute trip with later time.
                    </div>
                ) : leg.arrivalAfterDeparture ? (
                    <div className="arrival-after-departure">
                        <span className="exclamation">
                            <PriorityHighIcon />
                        </span>
                        {leg.mode} departure is before planned arrival
                    </div>
                ) : (<></>)
                }
                {averageDelayValue !== null && (
                    <div>
                        +{averageDelayValue} min
                    </div>
                )}
                <div 
                    onClick={() => setDeparturesOpen(!departuresOpen)}
                >
                    <FontAwesomeIcon icon={faAngleDown} className={departuresOpen ? "" : "rotate90"}/>
                    <DepartureBoardIcon 
                        className="departure-icon" 
                    />
                    Other departures
                </div>
                <div>
                    {departuresOpen && leg?.otherOptions?.departures.map((departure, index) => (
                        <>
                            {leg.otherOptions?.currentIndex !== undefined && leg?.otherOptions?.currentIndex - 1 <= index && leg?.otherOptions?.currentIndex + 2 >= index && (
                                <div className={leg?.otherOptions?.currentIndex === index ? "selected" : ""} onClick={() => recalculatePattern(index)}>
                                    {departure.departureTime}
                                </div>

                            )}
                        </>
                    ))}
                    {departuresOpen && (
                        <button
                            onClick={moreDeparturesClick}
                        >
                            More departures
                        </button>
                    )}
                </div>
            </div>
            <div>
                <div 
                    onClick={() => setStopsOpen(!stopsOpen)}
                >
                    <FontAwesomeIcon icon={faAngleDown} className={stopsOpen ? "" : "rotate90"}/>
                    <span className="station-icon">
                        <div className="station-square">
                        </div>
                    </span>
                    {((leg.serviceJourney?.quays.length ?? 0) + 1)} Stops
                </div>
                <div>
                    {stopsOpen && leg.serviceJourney?.quays.map(quay => (
                        <div className="stop">
                            <div className="timeline-dot public"/>
                            {quay.name}
                        </div>
                    ))}
                </div>
            </div>
            <div>
                <FontAwesomeIcon icon={faStopwatch} />
                {(leg.duration / 60).toFixed(0)} min
                <FontAwesomeIcon icon={faRoute} />
                {(leg.distance / 1000).toFixed(1)} km
            </div>
            <div className="waystop">
                {new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} {leg.toPlace?.name}
            </div>
        </div>
    );
}
export default PublicTransportDetail;

/** End of file PublicTransportDetail.tsx */
