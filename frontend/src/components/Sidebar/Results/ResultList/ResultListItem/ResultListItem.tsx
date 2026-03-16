/**
 * @file ResultListItem.tsx
 * @brief Displays a single trip pattern summary in the results list
 * @author Andrea Svitkova (xsvitka00)
 */

import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { IconButton } from "@mui/material";
import { TripPattern } from "../../../../types/types";
import Timeline from "../Timeline/Timeline";
import CustomTooltip from '../../../../CustomTooltip/CustomTooltip';
import { useTranslation } from 'react-i18next';
import "./ResultListItem.css"

type ResultListItemProps = {
    pattern: TripPattern;           // Trip pattern data
    selected?: boolean;             // Indicates whether the item is currently selected
    onClick?: () => void;           // Callback triggered when the list item is clicked
    onClickDetail?: () => void;     // Callback triggered when the detail button is clicked
}

function ResultListItem({
    pattern,
    selected,
    onClick,
    onClickDetail
} : ResultListItemProps) {
    // Translation function
    const { t } = useTranslation();

    return (
        <div 
            className={"pattern " + (selected ? "selected" : "")}
            onClick={onClick}
        >
            {/* Footer displaying trip start time and potential warnings */}
            <div className="pattern-footer">
                {/* Trip start time */}
                <span className="time">
                    {new Date(pattern.legs[0]?.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                {/* Warning icon if walking or cycling distance is too long */}
                {(pattern?.tooLongBikeDistance || pattern?.tooLongWalkDistance) && (
                    <span className="triangle-exclamation">
                        <CustomTooltip title= {pattern?.tooLongWalkDistance ? t("resultsInfo.warningFoot") : t("resultsInfo.warningBicycle")}>
                            <WarningAmberIcon />
                        </CustomTooltip>
                    </span>
                )}
            </div>
            <div className="pattern-content">
                {/* Timeline visualization of trip legs */}
                <Timeline 
                    totalDuration={pattern.totalDuration}
                    legs={pattern.legs}
                />

                <div className="pattern-info-wrapper">
                    {/* Total trip duration */}
                    <CustomTooltip title={t("tooltips.results.resultList.duration")}>
                        <span>
                            <AccessTimeIcon sx={{ color: 'var(--color-icons-darker)' }} />
                            {(() => {
                                const totalMinutes = Math.round(pattern.totalTime / 60);
                                const h = Math.floor(totalMinutes / 60);
                                const m = totalMinutes % 60;
                                return h > 0 ? `${h}:${m.toString().padStart(2, "0")}` : `${m} min`;
                            })()}
                        </span>
                    </CustomTooltip>

                    {/* Total trip distance */}
                    <CustomTooltip title={t("tooltips.results.resultList.distance")}>
                        <span>
                            <RouteIcon sx={{ color: 'var(--color-icons-darker)' }} />
                            {(pattern.totalDistance / 1000).toFixed(1)} km
                        </span>
                    </CustomTooltip>

                     {/* Number of transfers */}
                    {pattern?.numOfTransfers !== null && (
                        <CustomTooltip title={t("tooltips.results.resultList.transfers")}>
                            <span>
                                <SwapHorizIcon sx={{ color: 'var(--color-icons-darker)' }} />
                                {pattern.numOfTransfers}
                            </span>
                        </CustomTooltip>
                    )}
                </div>
            </div>
            <div className="pattern-footer">
                {/* Trip end time */}
                <span className="time">
                    {new Date(pattern.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>

                {/* Detail button */}
                <span className="hidden detail-span">
                    <CustomTooltip title={t("tooltips.results.detailButton")}>
                        <IconButton 
                            className="detail-button"
                            onClick={onClickDetail}
                        >
                            {t("resultsInfo.detail")}
                        </IconButton>
                    </CustomTooltip>
                </span>
            </div>
        </div>
    );
}

export default ResultListItem;

/** End of file ResultListItem.tsx */
