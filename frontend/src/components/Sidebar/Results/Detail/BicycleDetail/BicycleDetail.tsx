/**
 * @file BicycleDetail.tsx
 * @brief Displays the detail section for a bicycle leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from "../../../Planning/Icons/Icons";
import { useSettings } from "../../../../SettingsContext";
import { useInput } from "../../../../InputContext";
import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import LockOutlineIcon from '@mui/icons-material/LockOutline';

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
    const { useOwnBike } = useInput();
    const { bikeLockTime, bikesharingLockTime } = useSettings();
    
    useVerticalTimeLineHandle(
        bicycleRef,
        leg,
        setVerticalTimeline,
        index,
        30
    );

    const lockTime = useOwnBike ? bikeLockTime : bikesharingLockTime;

    return (
        <div
            ref={bicycleRef}
        >
            <div className="bicycle-detail">
                {!useOwnBike && (
                    <div className="detail-lock">
                        <LockOpenIcon/> {lockTime} min unlock time
                    </div>
                )}
                {timelineIcons["bicycle"]}
                <div className="detail-time-distance">
                    <div className="detail-time">
                        <AccessTimeIcon />
                        {(leg.duration / 60).toFixed(0)} min
                    </div>
                    <div className="detail-distance">
                        <RouteIcon />
                        {(leg.distance / 1000).toFixed(1)} km
                    </div>
                </div>
                <div className="detail-lock">
                    <LockOutlineIcon/> {lockTime} min lock time
                </div>
            </div>
        </div>
    );
}
export default BicycleDetail;

/** End of file BicycleDetail.tsx */
