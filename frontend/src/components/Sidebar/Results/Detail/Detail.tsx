/**
 * @file Detail.tsx
 * @brief Renders the trip detail with timeline and leg components
 * @author Andrea Svitkova (xsvitka00)
 */

import { Fragment, useEffect, useState } from "react";
import type { Leg, VerticalTimeline } from "../../../types/types";
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
    recalculatePattern: (selectedIndex: number, legIndex: number) => void;  // Callback used to recalculate pattern when selecting alternative departures
}

function Detail({
    recalculatePattern
} : DetailProps) {
    // Waypoints entered by the user
    const { waypoints } = useInput();

    // Setter for selecting a public transport leg
    const { setPublicLegIndex, pattern } = useResult();

    // Counter used to track which waypoint should be displayed
    let waypointCount = 0;
    
    // State representing the vertical timeline segments
    const [verticalTimeline, setVerticalTimeline] = useState<VerticalTimeline[]>(
        pattern?.originalLegs.map(leg => ({
            color: leg.color,
            length: 60,
            mode: leg.mode,
            artificial: leg.artificial
        }))
    );

    // Filter out non wait legs
    const nonWaitLegs = pattern?.originalLegs.filter(l => l.mode != "wait");

    // State storing heights of individual Waystop components
    const [waystopHeights, setWaystopHeights] = useState<number[]>(
        Array((nonWaitLegs.length ?? -1) + 1).fill(30)
    );

    // Find index of a given leg within non wait legs
    const findIndex = (leg: Leg) => nonWaitLegs.findIndex(l => l === leg);

    // Update height of a specific waystop
    const setHeight = (index: number, value: number) => {
        setWaystopHeights(prev => {
            // Skip update if index is invalid or value unchanged
            if (index < 0 || index >= prev.length || prev[index] === value) {
                return prev;
            }

            const copy = [...prev];
            copy[index] = value;
            return copy;
        });
    };

    /**
     * Compute vertical offset between two adjacent waystops
     */
    const computeOffset = (leg: Leg) => {
        const index = findIndex(leg);
        const prevHeight = waystopHeights[index] / 2;
        const nextHeight = waystopHeights[index + 1] / 2;

        // Compute vertical offset between two adjacent waystops
        return prevHeight + nextHeight;
    }

    /**
     * Update vertical timeline when trip pattern changes
     */
    useEffect(() => {
        setVerticalTimeline(
            pattern?.originalLegs.map(leg => ({
                color: leg.color,
                length: 60,
                mode: leg.mode,
                artificial: leg.artificial
            }))
        );
        setWaystopHeights(Array((nonWaitLegs.length ?? -1) + 1).fill(30));
    }, [pattern, nonWaitLegs.length]);

    return (
        <div className="detail-wrapper">

            {/* Vertical timeline */}
            <VerticalTimelineComponent 
                verticalTimeline={verticalTimeline}
                offset={Math.floor(waystopHeights[0] / 2)}
            />
            <div className="detail-patterns">
                {pattern?.originalLegs.map((leg, index) => {
                    /** Mode of the previous and next legs */
                    const previousLegMode = index > 0 ? pattern.originalLegs[index - 1].mode : null;
                    const nextLegMode = index < pattern.originalLegs.length - 1 ? pattern.originalLegs[index + 1].mode : null;
                   
                    // Determines whether an intermediate waypoint should be displayed
                    let displayWaypoint = false;

                    // Consecutive walking or cycling legs share waypoints
                    if (previousLegMode !== null && ["foot", "bicycle"].includes(previousLegMode) && ["foot", "bicycle"].includes(leg.mode)) {
                        waypointCount++;
                        displayWaypoint = index !== pattern.originalLegs.length - 1 || leg.mode == "foot";
                        if (displayWaypoint) {
                            console.log(index);
                        }
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
                                    updateHeight={(v) => setHeight(0, v)}
                                />
                            )}

                            {/* Intermediate waypoint */}
                            {displayWaypoint && !leg.artificial && (
                                <Waystop
                                    time={time}
                                    name={waypoints[waypointCount]?.displayName}
                                    updateHeight={(v) => setHeight(findIndex(leg), v)}
                                />
                            )}

                            {/* Render leg component based on transport mode */}
                            {leg.mode === "foot" ? (
                                !leg.artificial && (
                                    <WalkDetail
                                        leg={leg}
                                        setVerticalTimeline={setVerticalTimeline}
                                        index={index}
                                        offset={computeOffset(leg)}
                                    />
                                )
                            ) : leg.mode === "bicycle" ? (
                                <BicycleDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                    displayUnlockTime={previousLegMode === "wait"}
                                    displayLockTime={nextLegMode === "wait"}
                                    offset={computeOffset(leg)}
                                />
                            ) : leg.mode === "wait" ? (
                                <Waystop
                                    time={previousLegMode === "bicycle" ? endTime : time}
                                    name={leg.bikeStationInfo?.bikeStations[leg.bikeStationInfo.selectedBikeStationIndex].place.name}
                                    updateHeight={(v) => setHeight(findIndex(pattern?.originalLegs[index + 1]), v)}
                                />
                            ) : leg.mode === "transfer" ? (
                                <Transfer
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                    offset={computeOffset(leg)}
                                />
                            ) : (
                                <PublicTransportDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                    moreDeparturesClick={() => setPublicLegIndex(index)}
                                    recalculatePattern={(selectedIndex: number) => recalculatePattern(selectedIndex, index)}
                                    waystopHeightIndex={findIndex(leg)}
                                    setHeight={setHeight}
                                    offset={computeOffset(leg)}
                                />
                            )}

                            {/* Destination waypoint */}
                            {index === pattern.originalLegs.length - 1 && !leg.artificial && (
                                <Waystop
                                    time={endTime}
                                    name={waypoints[waypointCount + 1]?.displayName}
                                    updateHeight={(v) => setHeight(waystopHeights.length - 1, v)}
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
