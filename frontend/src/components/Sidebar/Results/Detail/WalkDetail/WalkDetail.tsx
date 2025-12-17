/**
 * @file WalkDetail.tsx
 * @brief Displays the detail section for a walk leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRoute, faStopwatch } from "@fortawesome/free-solid-svg-icons";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";

type WalkDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function WalkDetail({
    leg,
    setVerticalTimeline,
    index
} : WalkDetailProps) {
    const walkDetailRef = useRef<HTMLDivElement>(null);

    useVerticalTimeLineHandle(
        walkDetailRef,
        leg,
        setVerticalTimeline,
        index,
        27
    );

    return (
        <div
            ref={walkDetailRef}
        >
         <div>
            <FontAwesomeIcon icon={faStopwatch} />
            {(leg.duration / 60).toFixed(0)} min
            <FontAwesomeIcon icon={faRoute} />
            {(leg.distance / 1000).toFixed(1)} km
        </div>
        </div>
    );
}
export default WalkDetail;

/** End of file WalkDetail.tsx */
