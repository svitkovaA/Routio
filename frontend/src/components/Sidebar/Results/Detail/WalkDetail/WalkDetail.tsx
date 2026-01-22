/**
 * @file WalkDetail.tsx
 * @brief Displays the detail section for a walk leg
 * @author Andrea Svitkova (xsvitka00)
 */

import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from '../../../Planning/Icons/Icons';

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
            <div className="detail-time-distance">
                {timelineIcons["foot"]}
                <div className="detail-time">
                    <AccessTimeIcon />
                    {(leg.duration / 60).toFixed(0)} min
                </div>
                <div className="detail-distance">
                    <RouteIcon />
                    {(leg.distance / 1000).toFixed(1)} km
                </div>
            </div>
        </div>
    );
}
export default WalkDetail;

/** End of file WalkDetail.tsx */
