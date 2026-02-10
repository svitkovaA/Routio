/**
 * @file Detail.tsx
 * @brief Renders the full trip detail view with timeline and leg components
 * @author Andrea Svitkova (xsvitka00)
 */

import { Fragment, useEffect, useState } from "react";
import { TripPattern, VerticalTimeline } from "../../../types/types";
import PublicTransportDetail from "./PublicTransportDetail/PublicTransportDetail";
import WalkDetail from "./WalkDetail/WalkDetail";
import BicycleDetail from "./BicycleDetail/BicycleDetail";
import VerticalTimelineComponent from "./VerticalTimelineComponent/VerticalTimelineComponent";
import Transfer from "./Transfer/Transfer";
import { useInput } from "../../../InputContext";
import Waystop from "./Waystop/Waystop";
import "./Detail.css"
import { useResult } from "../../../ResultContext";

type DetailProps = {
    tripPattern: TripPattern;
    recalculatePattern: (selectedIndex: number, legIndex: number) => void;
}

function Detail({ 
    tripPattern, 
    recalculatePattern
} : DetailProps) {
    const { waypoints } = useInput();

    const { setPublicLegIndex } = useResult();

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
                        <Fragment key={`${index}`}>
                            {index === 0 && (
                                <Waystop
                                    time={time}
                                    name={waypoints[waypointCount].displayName}
                                />
                            )}
                            {displayWaypoint && (
                                <Waystop
                                    time={time}
                                    name={waypoints[waypointCount].displayName}
                                />
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
                                <Waystop
                                    time={previousLegMode === "bicycle" ? endTime :time}
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

                            {index === tripPattern.originalLegs.length - 1 && (
                                <Waystop
                                    time={endTime}
                                    name={waypoints[waypointCount + 1].displayName}
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
