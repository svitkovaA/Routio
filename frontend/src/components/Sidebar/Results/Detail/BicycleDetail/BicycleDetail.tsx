/**
 * @file BicycleDetail.tsx
 * @brief Displays the detail section for a bicycle leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from "../../../Planning/Icons/Icons";

type BicycleDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function BicycleDetail({
    leg,
    setVerticalTimeline,
    index
} : BicycleDetailProps) {
    const bicycleRef = useRef<HTMLDivElement>(null);
    
    useVerticalTimeLineHandle(
        bicycleRef,
        leg,
        setVerticalTimeline,
        index
    );

    return (
        <div
            ref={bicycleRef}
        >
            {timelineIcons["bicycle"]}
            bike
        </div>
    );
}
export default BicycleDetail;

/** End of file BicycleDetail.tsx */
