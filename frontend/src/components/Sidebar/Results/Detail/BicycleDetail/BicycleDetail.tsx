/**
 * @file BicycleDetail.tsx
 * @brief Displays the detail section for a bicycle leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef } from "react";
import { useTranslation } from "react-i18next";
import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import LockOutlineIcon from '@mui/icons-material/LockOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import type { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from "../../../Planning/Icons/IconMappings";
import { useSettings } from "../../../../Contexts/SettingsContext";
import { useInput } from "../../../../Contexts/InputContext";
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useResult } from "../../../../Contexts/ResultContext";
import ElevationProfile from "../Elevation/ElevationProfile";
import "./BicycleDetail.css";

type BicycleDetailProps = {
    leg: Leg;                       // Bicycle leg displayed in the detail
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;  // Setter used to update vertical timeline segments
    index: number;                  // Index of the leg within the trip pattern
    displayUnlockTime: boolean;     // Indicates whether unlock time should be displayed 
    displayLockTime: boolean;       // Indicates whether lock time should be displayed
    offset: number;                 // Vertical timeline offset
};

function BicycleDetail({
    leg,
    setVerticalTimeline,
    index,
    displayUnlockTime,
    displayLockTime,
    offset
} : BicycleDetailProps) {
    // Translation function
    const { t } = useTranslation();

    // Reference to the element used for timeline height synchronization
    const bicycleRef = useRef<HTMLDivElement>(null);

    // User input context
    const { useOwnBike } = useInput();

    // Settings context
    const { bikeLockTime, bikesharingLockTime } = useSettings();

    // Result context
    const {
        polyInfo,
        openElevation,
        pattern
    } = useResult();

    // Polyline information in this leg
    const concPolyInfo = polyInfo[index];
    
    // Synchronizes vertical timeline segment length with the height of the bicycle detail component
    useVerticalTimeLineHandle(
        bicycleRef,
        leg,
        setVerticalTimeline,
        index,
        offset
    );

    // Determines bike lock duration
    const lockTime = useOwnBike ? bikeLockTime : bikesharingLockTime;

    const waitLeg = (displayUnlockTime && pattern?.originalLegs) 
        ? pattern?.originalLegs[index - 1] ?? null 
        : null;

    return (
        <div
            ref={bicycleRef}
        >
            <div className="bicycle-detail">
                {/* Bicycle icon */}
                {timelineIcons["bicycle"]}

                <div className="bicycle-leg-detail">
                    <div className="bicycle-leg-left">
                        {/* Time required to unlock the bicycle */}
                        {displayUnlockTime && (
                            <CustomTooltip title={t("tooltips.detail.bicycle.lockTime")}>
                                <div className="detail-lock">
                                    <LockOpenIcon/> {lockTime} min {t("detailInfo.bicycle.unlockTime")}
                                </div>
                            </CustomTooltip>
                        )}

                        {waitLeg !== null && (() => {
                            const selectedStationIndex = waitLeg.bikeStationInfo?.selectedBikeStationIndex;
                            if (selectedStationIndex === undefined) {
                                return null;
                            }

                            const selectedStation = waitLeg.bikeStationInfo?.bikeStations[selectedStationIndex];
                            if (selectedStation === undefined) {
                                return null;
                            }
                            return (
                                <>
                                    <div className="bike-card">
                                        <div className="item">
                                            <div className="label">{t("map.now")}:</div>
                                            <div className="value current">
                                                {selectedStation.place.bikesAvailable}
                                            </div>
                                        </div>

                                        <div className="item">
                                            <div className="label">{t("map.predicted")}:</div>
                                            <div className="value predicted">
                                                <div className="value-warning">
                                                    <span>
                                                        {selectedStation.place.predictedBikes !== null ? (
                                                                selectedStation.place.predictedBikes
                                                        ) : (
                                                            <CustomTooltip title={t("tooltips.map.noPrediction")}>
                                                                <span>
                                                                    --
                                                                </span>
                                                            </CustomTooltip>
                                                        )}
                                                    </span>
                                                    
                                                    {waitLeg.zeroBikesPredicted && (
                                                        <CustomTooltip title={t("tooltips.detail.bicycle.zeroWarning")}>
                                                            <WarningAmberIcon className="zero-warning"/>
                                                        </CustomTooltip>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            );
                        })()}

                        {/* Duration and distance */}
                        <div className={"detail-time-distance " + (waitLeg !== null ? "origin" : "")}>
                            <CustomTooltip title={t("tooltips.detail.segment.duration")}>
                                <div className="detail-time">
                                    <AccessTimeIcon />
                                    {(() => {
                                        const totalMinutes = Math.round(leg.duration / 60);
                                        const h = Math.floor(totalMinutes / 60);
                                        const m = totalMinutes % 60;
                                        return h > 0 ? `${h}:${m.toString().padStart(2, "0")}` : `${m} min`;
                                    })()}
                                </div>       
                            </CustomTooltip>

                            <CustomTooltip title={t("tooltips.detail.segment.distance")}>
                                <div className="detail-distance">
                                    <RouteIcon />
                                    {(leg.distance / 1000).toFixed(1)} km
                                </div>
                            </CustomTooltip>
                        </div>

                        {/* Time required to lock the bicycle */}
                        {displayLockTime && (
                            <CustomTooltip title={t("tooltips.detail.bicycle.unlockTime")}>
                                <div className="detail-lock">
                                    <LockOutlineIcon/> {lockTime} min {t("detailInfo.bicycle.lockTime")}
                                </div>
                            </CustomTooltip>
                        )}
                    </div>
                </div>

                {/* Elevation profile of the bicycle segment */}
                <ElevationProfile
                    polyInfo={concPolyInfo}
                    legIndex={index}
                    openElevation={(value: boolean) => openElevation(index, value)}
                />
            </div>
        </div>
    );
}
export default BicycleDetail;

/** End of file BicycleDetail.tsx */
