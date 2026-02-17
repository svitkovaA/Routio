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
    pattern: TripPattern;
    selected?: boolean;
    onClick?: () => void;
    onClickDetail?: () => void;
}

function ResultListItem({
    pattern,
    selected,
    onClick,
    onClickDetail
} : ResultListItemProps) {
    const { t } = useTranslation();

    return (
        <div 
            className={"pattern " + (selected ? "selected" : "")}
            onClick={onClick}
        >
            <div className="pattern-footer">
                <span className="time">
                    {new Date(pattern.legs[0]?.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                {(pattern?.tooLongBikeDistance || pattern?.tooLongWalkDistance) && (
                    <span className="triangle-exclamation">
                        <WarningAmberIcon />
                    </span>
                )}
            </div>
            <div className="pattern-content">
                <Timeline 
                    totalDuration={pattern.totalDuration}
                    legs={pattern.legs}
                />
                <div className="pattern-info-wrapper">
                    <CustomTooltip title={t("tooltips.results.resultList.duration")}>
                        <span>
                            <AccessTimeIcon sx={{ color: 'var(--color-icons-darker)' }} />
                            {Math.round(pattern.totalDuration / 60)} min
                        </span>
                    </CustomTooltip>

                    <CustomTooltip title={t("tooltips.results.resultList.distance")}>
                        <span>
                            <RouteIcon sx={{ color: 'var(--color-icons-darker)' }} />
                            {(pattern.totalDistance / 1000).toFixed(1)} km
                        </span>
                    </CustomTooltip>

                    {pattern?.numOfTransfers !== undefined && (
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
                <span className="time">
                    {new Date(pattern.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
                <span className="hidden detail-span">
                    <CustomTooltip title={t("tooltips.results.detailButton")}>
                        <IconButton 
                            className="detail-button"
                            onClick={onClickDetail}
                        >
                            Detail
                        </IconButton>
                    </CustomTooltip>
                </span>
            </div>
        </div>
    );
}

export default ResultListItem;

/** End of file ResultListItem.tsx */
