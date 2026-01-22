/**
 * @file PublicTransportDetail.tsx
 * @brief Displays the detail section for a public transport leg
 * @author Andrea Svitkova (xsvitka00)
 */

import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import { useEffect, useRef, useState } from "react";
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import DepartureBoardIcon from '@mui/icons-material/DepartureBoard';
import { Leg, VerticalTimeline } from "../../../../types/types";
import "./PublicTransportDetail.css";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from '../../../Planning/Icons/Icons';
import Waystop from '../Waystop/Waystop';

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

    useEffect(() => setStopsOpen(false), [leg]);

    return (
        <div
            ref={publicTransportDetailRef} className="public-transport-detail"
        >
            <Waystop
                time={new Date(leg.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                name={leg.fromPlace?.name}
            />
            {timelineIcons[leg.mode]}
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
                    <KeyboardArrowDownIcon className={departuresOpen ? "" : "rotate90"}/>
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
                    <KeyboardArrowDownIcon className={stopsOpen ? "" : "rotate90"}/>
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
            <div className="detail-time-distance">
                <div className="detail-time">
                    <AccessTimeIcon />
                    {(leg.duration / 60).toFixed(0)} min
                </div>
                <div className="detail-distance">
                    <RouteIcon />
                    {(leg.distance / 1000).toFixed(1)} km
                </div>
            </div>
            <Waystop
                time={new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                name={leg.toPlace?.name}
            />
        </div>
    );
}
export default PublicTransportDetail;

/** End of file PublicTransportDetail.tsx */
