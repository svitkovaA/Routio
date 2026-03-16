/**
 * @file Transfer.tsx
 * @brief Displays the transfer section between trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from "../../../Planning/Icons/Icons";
import { useTranslation } from "react-i18next";
import "./Transfer.css"

type TransferProps = {
    leg: Leg;           // Transfer leg between two transport segments
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void; // Setter used to update vertical timeline segments
    index: number;      // Index of the leg within the trip pattern
}

function Transfer({
    leg,
    setVerticalTimeline,
    index,
} : TransferProps) {
    // Translation function
    const { t } = useTranslation();

    // Reference to the transfer element
    const transferRef = useRef<HTMLDivElement>(null);

    // Synchronizes the vertical timeline segment with the height of the transfer component
    useVerticalTimeLineHandle(
        transferRef,
        leg,
        setVerticalTimeline,
        index,
        30
    );

    return (
        <div
            className="transfer"
            ref={transferRef}
        >
            {/* Transfer icon */}
            {timelineIcons["transfer"]}

            {/* Transfer icon */}
            {t("detailInfo.publicTransport.transfer")}
        </div>
    );
}
export default Transfer;

/** End of file Transfer.tsx */
