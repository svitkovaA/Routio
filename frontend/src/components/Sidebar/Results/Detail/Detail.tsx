/**
 * @file Detail.tsx
 * @brief Renders the full trip detail view with timeline and leg components
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { TripPattern, VerticalTimeline, Waypoint } from "../../../types/types";
import PublicTransportDetail from "./PublicTransportDetail/PublicTransportDetail";
import WalkDetail from "./WalkDetail/WalkDetail";
import BicycleDetail from "./BicycleDetail/BicycleDetail";
import WaitDetail from "./WaitDetail/WaitDetail";
import VerticalTimelineComponent from "./VerticalTimelineComponent/VerticalTimelineComponent";
import Transfer from "./Transfer/Transfer";
import "./Detail.css"
import { useInput } from "../../../InputContext";

type DetailProps = {
    tripPattern: TripPattern;
    setPublicLegIndex: (value: number) => void;
    recalculatePattern: (selectedIndex: number, legIndex: number) => void;
}

function Detail({ 
    tripPattern, 
    setPublicLegIndex,
    recalculatePattern
} : DetailProps) {
    const { waypoints } = useInput();

    let waypointCount = 0;

    const [verticalTimeline, setVerticalTimeline] = useState<VerticalTimeline[]>(
        tripPattern.originalLegs.map(leg => ({
            color: leg.color,
            length: 60,
            mode: leg.mode
        }))
    );

    useEffect(() => {
        setVerticalTimeline(
            tripPattern.originalLegs.map(leg => ({
                color: leg.color,
                length: 60,
                mode: leg.mode
            }))
        );
    }, [tripPattern]);

    return (
        <div className="detail-wrapper">
            <VerticalTimelineComponent verticalTimeline={verticalTimeline} />
            <div className="detail-patterns">
                {tripPattern.originalLegs.map((leg, index) => {
                    const previousLegMode = index > 0 ? tripPattern.originalLegs[index - 1].mode : null;
                    let displayWaypoint = false;
                    if (previousLegMode === leg.mode && (leg.mode === "foot" || leg.mode === "bicycle")) {
                        waypointCount++;
                        displayWaypoint = index !== tripPattern.originalLegs.length - 1 || !!leg.walkMode;
                    }
                    const time = new Date(leg.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                    const endTime = new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

                    return (
                        <>
                            {index === 0 && (
                                <div className="waystop">
                                    {time} {waypoints[waypointCount].displayName}
                                </div>
                            )}
                            {displayWaypoint && (
                                <div className="waystop">
                                    {time} {waypoints[waypointCount].displayName}
                                </div>
                            )}

                            {leg.mode === "foot" ? (
                                <WalkDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                />
                            ) : leg.mode === "bicycle" ? (
                                <BicycleDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
                                />
                            ) : leg.mode === "wait" ? (
                                <WaitDetail
                                    leg={leg}
                                    setVerticalTimeline={setVerticalTimeline}
                                    index={index}
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

                            {index === tripPattern.originalLegs.length - 1 && (
                                <div className="waystop">
                                    {endTime} {waypoints[waypointCount + 1].displayName}
                                </div>
                            )}
                        </>
                    );
                })}
            </div>
        </div>
    );
}

export default Detail;

/** End of file Detail.tsx */
