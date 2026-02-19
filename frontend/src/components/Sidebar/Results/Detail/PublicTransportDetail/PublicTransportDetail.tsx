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
import { Leg, VerticalTimeline } from "../../../../types/types";
import { useVerticalTimeLineHandle } from "../VerticalTimelineComponent/VerticalTimeLineHandle";
import { timelineIcons } from '../../../Planning/Icons/Icons';
import Waystop from '../Waystop/Waystop';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CustomTooltip from '../../../../CustomTooltip/CustomTooltip';
import "./PublicTransportDetail.css";

type PublicTransportDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
    moreDeparturesClick: () => void;
    recalculatePattern: (selectedIndex: number) => void;
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

    const [stopsOpen, setStopsOpen] = useState<boolean>(false);
    const [departuresOpen, setDeparturesOpen] = useState<boolean>(false);
    const publicTransportDetailRef = useRef<HTMLDivElement>(null);

    const averageDelay = () => {
        if (!leg.delays) return null;

        const values = Object.values(leg.delays);
        if (values.length === 0) return null;

        const total = values.reduce((sum, v) => sum + v, 0);
        return Math.round(total / values.length);
    }

    const averageDelayValue = averageDelay();

    useVerticalTimeLineHandle(
        publicTransportDetailRef,
        leg,
        setVerticalTimeline,
        index,
        -30
    );

    useEffect(() => setStopsOpen(false), [leg]);

    const currentIndex = leg.otherOptions?.currentIndex;
    const departures = leg?.otherOptions?.departures;
    const moreResults = departures && currentIndex !== undefined && (currentIndex - 1 > 0 || currentIndex + 2 < departures.length - 1);

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
                <div className="detail-direction">
                    <div className="detail-public-code" style={{ backgroundColor: leg.color}}>
                        {leg.line?.publicCode}
                    </div>
                    <ArrowForwardIcon sx={{ fontSize: '18px' }}/> 
                    {leg.serviceJourney?.direction}
                </div>
                {averageDelayValue !== null && (
                    <div className={"delay-info " + (averageDelayValue !== 0 ? "delayed" : "")}>
                        +{averageDelayValue} min
                    </div>
                )}
            </div>
            <div>
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
                    {departuresOpen && (
                        <button
                            className="departure-button"
                            onClick={moreDeparturesClick}
                            disabled={!moreResults}
                        >
                            {t("detailInfo.publicTransport.moreDepartures")}
                        </button>
                    )}
                </div>
            </div>
            <div>
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
                            className="stop"
                        >
                            <div className="timeline-dot public"/>
                            {quay.name}
                        </div>
                    ))}
                </div>
            </div>
            <div className="detail-time-distance">
                <CustomTooltip title={t("tooltips.detail.segment.duration")}>
                    <div className="detail-time">
                        <AccessTimeIcon />
                        {(leg.duration / 60).toFixed(0)} min
                    </div>
                </CustomTooltip>

                <CustomTooltip title={t("tooltips.detail.segment.distance")}>
                    <div className="detail-distance">
                        <RouteIcon />
                        {(leg.distance / 1000).toFixed(1)} km
                    </div>
                </CustomTooltip>
            </div>
            <Waystop
                time={new Date(leg.aimedEndTime).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                name={leg.toPlace?.name}
            />
        </div>
    );
}
export default PublicTransportDetail;

/** End of file PublicTransportDetail.tsx */
