/**
 * @file WalkDetail.tsx
 * @brief Displays the detail section for a walk leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { useTranslation } from 'react-i18next';
import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import type { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from '../../../Planning/Icons/IconMappings';
import CustomTooltip from '../../../../CustomTooltip/CustomTooltip';
import ElevationProfile from "../Elevation/ElevationProfile";
import { useResult } from "../../../../Contexts/ResultContext";

type WalkDetailProps = {
    leg: Leg;           // Walking leg
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;  // Setter used to update the vertical timeline segments
    index: number;      // Index of the leg within the trip pattern
    offset: number;     // Vertical timeline offset
};

function WalkDetail({
    leg,
    setVerticalTimeline,
    index,
    offset
} : WalkDetailProps) {
    // Translation function
    const { t } = useTranslation();

    // Reference to the walking detail element
    const walkDetailRef = useRef<HTMLDivElement>(null);

    // Hook responsible for synchronizing the vertical timeline with the height of the walking detail component
    useVerticalTimeLineHandle(
        walkDetailRef,
        leg,
        setVerticalTimeline,
        index,
        offset
    );

    // Polyline elevation data
    const {
        polyInfo,
        openElevation
    } = useResult();

    // Polyline information for the current leg
    const concPolyInfo = polyInfo[index];

    return (
        <div
            ref={walkDetailRef}
        >
            <div className="detail-time-distance">
                {/* Walking mode icon */}
                {timelineIcons["foot"]}

                {/* Walking duration */}
                <CustomTooltip title={t("tooltips.detail.segment.duration")}>
                    <div className="detail-time">
                        <AccessTimeIcon />
                        {(() => {
                            const totalMinutes = Math.round(leg.duration / 60);
                            const h = Math.floor(totalMinutes / 60);
                            const m = totalMinutes % 60;
                            return h > 0 ? `${h}:${m.toString().padStart(2, "0")}` : m > 0 ? `${m} min` : `${leg.duration} s`;
                        })()}
                    </div>
                </CustomTooltip>

                {/* Walking distance */}
                <CustomTooltip title={t("tooltips.detail.segment.distance")}>
                    <div className="detail-distance">
                        <RouteIcon />
                        {(() => {
                            const distance = (leg.distance / 1000).toFixed(1);
                            return leg.distance < 1000 ? `${leg.distance.toFixed(0)} m` : `${distance} km`
                        })()}
                    </div>
                </CustomTooltip>
            </div>

            {/* Elevation profile of the walking segment */}
            <ElevationProfile
                polyInfo={concPolyInfo}
                legIndex={index}
                openElevation={(value: boolean) => openElevation(index, value)}
            />
        </div>
    );
}
export default WalkDetail;

/** End of file WalkDetail.tsx */
