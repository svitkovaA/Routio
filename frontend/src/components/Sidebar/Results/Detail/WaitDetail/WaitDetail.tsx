/**
 * @file WaitDetail.tsx
 * @brief Displays the detail section for a wait leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";

type WaitDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function WaitDetail({
    leg,
    setVerticalTimeline,
    index
} : WaitDetailProps) {
    const waitRef = useRef<HTMLDivElement>(null);

    useVerticalTimeLineHandle(
        waitRef,
        leg,
        setVerticalTimeline,
        index
    );

    return (
        <div
            ref={waitRef}
        >
            wait
        </div>
    );
}
export default WaitDetail;

/** End of file WaitDetail.tsx */
