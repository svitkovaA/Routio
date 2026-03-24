/**
 * @file Detail.tsx
 * @brief Renders the trip detail with timeline and leg components
 * @author Andrea Svitkova (xsvitka00)
 */

import { Fragment, useEffect, useState } from "react";
import { TripPattern, VerticalTimeline } from "../../../types/types";
import PublicTransportDetail from "./PublicTransportDetail/PublicTransportDetail";
import WalkDetail from "./WalkDetail/WalkDetail";
import BicycleDetail from "./BicycleDetail/BicycleDetail";
import VerticalTimelineComponent from "./VerticalTimelineComponent/VerticalTimelineComponent";
import Transfer from "./Transfer/Transfer";
import { useInput } from "../../../Contexts/InputContext";
import Waystop from "./Waystop/Waystop";
import { useResult } from "../../../Contexts/ResultContext";
import "./Detail.css"

type DetailProps = {
    tripPattern: TripPattern;                                               // Trip pattern displayed in the detail view
    recalculatePattern: (selectedIndex: number, legIndex: number) => void;  // Callback used to recalculate pattern when selecting alternative departures
}

function Detail({ 
    tripPattern, 
    recalculatePattern
} : DetailProps) {
    // Waypoints entered by the user
    const { waypoints } = useInput();

    // Setter for selecting a public transport leg
    const { setPublicLegIndex } = useResult();

    // Counter used to track which waypoint should be displayed
    let waypointCount = 0;
    
    // State representing the vertical timeline segments
    const [verticalTimeline, setVerticalTimeline] = useState<VerticalTimeline[]>(
        tripPattern?.originalLegs.map(leg => ({
            color: leg.color,
            length: 60,
            mode: leg.mode,
            artificial: leg.artificial
        }))
    );

    /**
     * Update vertical timeline when trip pattern changes
     */
    useEffect(() => {
        setVerticalTimeline(
            tripPattern?.originalLegs.map(leg => ({
                color: leg.color,
                length: 60,
                mode: leg.mode,
                artificial: leg.artificial
            }))
        );
    }, [tripPattern]);

    return (
        <div className="detail-wrapper">

            {/* Vertical timeline */}
            <VerticalTimelineComponent verticalTimeline={verticalTimeline} />
            <div className="detail-patterns">
                {tripPattern?.originalLegs.map((leg, index) => {
                    /** Mode of the previous and next legs */
                    const previousLegMode = index > 0 ? tripPattern.originalLegs[index - 1].mode : null;
                    const nextLegMode = index < tripPattern.originalLegs.length - 1 ? tripPattern.originalLegs[index + 1].mode : null;
                   
                    // Determines whether an intermediate waypoint should be displayed
                    let displayWaypoint = false;

                    // Consecutive walking or cycling legs share waypoints
                    if (previousLegMode === leg.mode && (leg.mode === "foot" || leg.mode === "bicycle")) {
                        waypointCount++;
                        displayWaypoint = index !== tripPattern.originalLegs.length - 1 || !!leg.walkMode;
                    }

                    // Start and end times
                    const time = new Date(leg.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                    const endTime = new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

                    return (
                        <Fragment key={`${index}`}>
                            {/* Starting waypoint */}
                            {index === 0 && !leg.artificial && (
                                <Waystop
                                    time={time}
                                    name={waypoints[waypointCount]?.displayName}
                                />
                            )}

                            {/* Intermediate waypoint */}
                            {displayWaypoint && !leg.artificial && (
                                <Waystop
                                    time={time}
                                    name={waypoints[waypointCount]?.displayName}
                                />
                            )}

                            {/* Render leg component based on transport mode */}
                            {leg.mode === "foot" ? (
                                !leg.artificial && (
                                    <WalkDetail
                                        leg={leg}
                                        setVerticalTimeline={setVerticalTimeline}
                                        index={index}
                                    />
                                )
                            ) : leg.mode === "bicycle" ? (
                                <BicycleDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                    displayUnlockTime={previousLegMode === "wait"}
                                    displayLockTime={nextLegMode === "wait"}
                                />
                            ) : leg.mode === "wait" ? (
                                <Waystop
                                    time={previousLegMode === "bicycle" ? endTime : time}
                                    name={leg.bikeStationInfo?.bikeStations[leg.bikeStationInfo.selectedBikeStationIndex].place.name}
                                />
                            ) : leg.mode === "transfer" ? (
                                <Transfer
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                />
                            ) : (
                                <PublicTransportDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                    moreDeparturesClick={() => setPublicLegIndex(index)}
                                    recalculatePattern={(selectedIndex: number) => recalculatePattern(selectedIndex, index)}
                                />
                            )}

                            {/* Destination waypoint */}
                            {index === tripPattern.originalLegs.length - 1 && !leg.artificial && (
                                <Waystop
                                    time={endTime}
                                    name={waypoints[waypointCount + 1]?.displayName}
                                />
                            )}
                        </Fragment>
                    );
                })}
            </div>
        </div>
    );
}

export default Detail;

/** End of file Detail.tsx */
