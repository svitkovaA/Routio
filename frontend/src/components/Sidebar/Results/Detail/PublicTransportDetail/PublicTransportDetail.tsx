/**
 * @file PublicTransportDetail.tsx
 * @brief Displays the detail section for a public transport leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef, useState } from "react";
import { useTranslation } from 'react-i18next';
import RouteIcon from '@mui/icons-material/Route';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import DepartureBoardIcon from '@mui/icons-material/DepartureBoard';
import HistoryIcon from '@mui/icons-material/History';
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from '../../../Planning/Icons/Icons';
import Waystop from '../Waystop/Waystop';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CustomTooltip from '../../../../CustomTooltip/CustomTooltip';
import { useSettings } from "../../../../Contexts/SettingsContext";
import "./PublicTransportDetail.css";

type PublicTransportDetailProps = {
    leg: Leg;                                               // Public transport leg displayed in the detail
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;  // Setter used to update vertical timeline segments
    index: number;                                          // Index of the leg within the trip pattern
    moreDeparturesClick: () => void;                        // Opens extended departure options
    recalculatePattern: (selectedIndex: number) => void;    // Recalculates trip pattern for a selected departure
}

function PublicTransportDetail({
    leg,
    setVerticalTimeline,
    index,
    moreDeparturesClick,
    recalculatePattern
} : PublicTransportDetailProps) {
    // Translation function
    const { t } = useTranslation();

    // State controlling collapsible sections
    const [stopsOpen, setStopsOpen] = useState<boolean>(false);
    const [departuresOpen, setDeparturesOpen] = useState<boolean>(false);
    const [historicalDelaysOpen, setHistoricalDelaysOpen] = useState<boolean>(false);

    // Reference to the element used for timeline height synchronization
    const publicTransportDetailRef = useRef<HTMLDivElement>(null);

    // Synchronizes vertical timeline segment length with the height of this detail component
    useVerticalTimeLineHandle(
        publicTransportDetailRef,
        leg,
        setVerticalTimeline,
        index,
        -30
    );

    // Settings context
    const { useHistoricalDelays } = useSettings();

    // Collapse stops list when a different leg is rendered
    useEffect(() => setStopsOpen(false), [leg]);

    // Collapse historical delays when a different leg is rendered
    useEffect(() => setHistoricalDelaysOpen(false), [leg]);

    // Currently selected departure index
    const currentIndex = leg.otherOptions?.currentIndex;

    // Available departure alternatives
    const departures = leg?.otherOptions?.departures;

    // Determines whether additional departures exist outside the currently displayed range
    const moreResults = (
        departures && currentIndex !== undefined &&
        (currentIndex - 1 > 0 || currentIndex + 2 < departures.length - 1)
    );

    return (
        <div
            ref={publicTransportDetailRef} className="public-transport-detail"
        >
            <Waystop
                time={new Date(leg.aimedStartTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                name={leg.fromPlace?.name}
            />
            {timelineIcons[leg.mode]}
            <div className="detail-trip-info">

                {/* Route direction and line information */}
                <div className="detail-direction">
                    <div className="detail-public-code" style={{ backgroundColor: leg.color}}>
                        {leg.line?.publicCode}
                    </div>
                    <ArrowForwardIcon sx={{ fontSize: '18px' }}/> 
                    {leg.serviceJourney?.direction}
                </div>

                {/* Current delay indicator */}
                {leg.delay !== undefined && (
                    <CustomTooltip title={t("tooltips.detail.publicTransport.currentDelay")}>
                        <div className={"delay-info " + (leg.delay > 0 ? "delayed" : "")}>
                            {leg.delay <= 0 ? (
                                t("detailInfo.publicTransport.historicalDelaysOnTime")
                            ) : (
                                `+${leg.delay} min`
                            )}
                        </div>
                    </CustomTooltip>
                )}
            </div>
            {/* Fare zones on this segment */}
            {leg.zone_ids && leg.zone_ids.length > 0 && (
                <div className="detail-zones">
                    {leg.zone_ids.length === 1 ? (
                        `${t("detailInfo.publicTransport.zone")}: ${leg.zone_ids[0]}`
                    ) : leg.zone_ids.length === 2 ? (
                        `${t("detailInfo.publicTransport.zones")}: ${leg.zone_ids.join(" + ")}`
                    ) : 
                        `${t("detailInfo.publicTransport.zones")}: ${leg.zone_ids.join(", ")}`
                    }
                </div>
            )}
            <div>
                {/* Warning messages */}
                {leg.nonContinuousDepartures ? (
                    <div className="warning-departures">
                        <span className="exclamation">
                            <PriorityHighIcon />
                        </span>
                        <span>
                            {t("detailInfo.publicTransport.nonContinuousDepartures")}
                        </span>
                    </div>
                ) : leg.arrivalAfterDeparture ? (
                    <div className="warning-departures">
                        <span className="exclamation">
                            <PriorityHighIcon />
                        </span>
                        <span>
                            {t(`detailInfo.publicTransport.modes.${leg.mode}`)} {t("detailInfo.publicTransport.arrivalAfterDeparture")}
                        </span>
                    </div>
                ) : (<></>)}

                {/* Toggle list of alternative departures */}
                <div 
                    onClick={() => setDeparturesOpen(!departuresOpen)}
                    className="detail-departures"
                >
                    <CustomTooltip title={departuresOpen ? t("tooltips.detail.publicTransport.closeOtherDepartures") : t("tooltips.detail.publicTransport.otherDepartures")}>
                        <KeyboardArrowDownIcon className={departuresOpen ? "" : "rotate90"}/>
                    </CustomTooltip>

                    <DepartureBoardIcon 
                        className="departure-icon" 
                        />
                    {t("detailInfo.publicTransport.otherDepartures")}
                </div>        
                <div className={departuresOpen ? "departure-box" : ""}>
                    {departuresOpen && leg?.otherOptions?.departures.map((departure, index) => {
                        if (currentIndex === undefined) {
                            return null;
                        } 

                        if (currentIndex - 1 > index || currentIndex + 2 < index) {
                            return null;
                        }

                        return (
                            <div 
                                key={`${index}`}
                                className={"departure-row" + (currentIndex === index ? " selected" : "")} 
                                onClick={() => recalculatePattern(index)}
                            >
                                <span className="departure-direction">
                                    {departure.direction}
                                </span>
                                <span className="departure-time">
                                    {new Date(departure.departureTime).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit",})}
                                </span>
                            </div>
                        );
                    })}
                    {departuresOpen && moreResults && (
                        <button
                            className="departure-button"
                            onClick={moreDeparturesClick}
                        >
                            {t("detailInfo.publicTransport.moreDepartures")}
                        </button>
                    )}
                </div>
            </div>
            <div>
                {(leg.serviceJourney?.quays.length ?? 0) >= 1 && (
                    <>
                        {/* Expandable list of stops served by the vehicle */}
                        <div 
                            onClick={() => setStopsOpen(!stopsOpen)}
                            className="detail-stops"
                        >
                            <CustomTooltip title={stopsOpen ? t("tooltips.detail.publicTransport.closeStopsOnRoute") : t("tooltips.detail.publicTransport.stopsOnRoute")}>
                                <KeyboardArrowDownIcon className={stopsOpen ? "" : "rotate90"}/>
                            </CustomTooltip>

                            <span className="station-icon">
                                <div className="station-square">
                                </div>
                            </span>
                            {((leg.serviceJourney?.quays.length ?? 0) + 1)} {t("detailInfo.publicTransport.stops")}
                        </div>
                        <div>
                            {stopsOpen && leg.serviceJourney?.quays.map((quay, index) => (
                                <div
                                    key={`${index}`}
                                    className={"stop " + (
                                        leg.serviceJourney?.startOffset !== undefined && 
                                        leg.serviceJourney.currentIndex !== null
                                        ? (leg.serviceJourney.currentIndex - leg.serviceJourney.startOffset) === index
                                            ? "current" 
                                            : (leg.serviceJourney.currentIndex - leg.serviceJourney.startOffset) > index
                                                ? "passed" : ""
                                        : "")
                                    }
                                >
                                    <div className="timeline-dot public"/>
                                    {quay.name}
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Historical delay statistics for this service */}
            {useHistoricalDelays && leg?.delays && Object.keys(leg.delays).length > 0 && (
                <>
                    <div
                        onClick={() => setHistoricalDelaysOpen(!historicalDelaysOpen)}
                        className="detail-historical-delays"
                    >
                        <CustomTooltip title={historicalDelaysOpen ? t("tooltips.detail.publicTransport.closeHistoricalDelays") : t("tooltips.detail.publicTransport.historicalDelays")}>
                            <KeyboardArrowDownIcon className={historicalDelaysOpen ? "" : "rotate90"}/>
                        </CustomTooltip>

                        <HistoryIcon 
                            className="historical-delays"
                        />
                        {t("detailInfo.publicTransport.historicalDelays")}
                    </div>

                    {historicalDelaysOpen && (
                        <div className="historical-delays-box">
                            {Object.entries(leg.delays!).map(([date, delay]) => (
                                <div 
                                    key={date}
                                    className="historical-delay-row"
                                >
                                    <span className="historical-date">
                                        {new Date(date).toLocaleDateString("sk-SK", {
                                            day: "2-digit",
                                            month: "2-digit"
                                        })}
                                    </span>

                                    <span className={"historical-delay " + (delay > 0 ? "delayed" : "")}>
                                        + {delay} min
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}

            {/* Duration and distance of the segment */}
            <div className="detail-time-distance">
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

            {/* Waystop */}
            <Waystop
                time={new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                name={leg.toPlace?.name}
            />
        </div>
    );
}
export default PublicTransportDetail;

/** End of file PublicTransportDetail.tsx */
