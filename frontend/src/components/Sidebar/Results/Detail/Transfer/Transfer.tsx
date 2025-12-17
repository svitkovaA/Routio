/**
 * @file Transfer.tsx
 * @brief Displays the transfer section between trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";

type TransferProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function PublicTransportDetail({
    leg,
    setVerticalTimeline,
    index,
} : TransferProps) {
    const transferRef = useRef<HTMLDivElement>(null);

    useVerticalTimeLineHandle(
        transferRef,
        leg,
        setVerticalTimeline,
        index,
        30
    );

    return (
        <div
            ref={transferRef}
        >
            transfer
        </div>
    );
}
export default PublicTransportDetail;

/** End of file Transfer.tsx */
