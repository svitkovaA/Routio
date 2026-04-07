/**
 * @file IconMappings.tsx
 * @brief Provides icons for transport modes and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import type { JSX } from "react";
import TrainIcon from '@mui/icons-material/Train';
import TramIcon from '@mui/icons-material/Tram';
import DirectionsBoatIcon from '@mui/icons-material/DirectionsBoat';
import TransferWithinAStationIcon from '@mui/icons-material/TransferWithinAStation';
import DirectionsTransitIcon from '@mui/icons-material/DirectionsTransit';
import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import type { Mode } from "../../../types/types";
import { MultimodalIcon } from "./Icons";

/**
 * Mapping of available planning modes to their corresponding icons
 */
export const modeIcons: {html: JSX.Element, value: Mode}[] = [{
        html: <MultimodalIcon />, 
        value: "multimodal"
    }, {
        html: 
            <div className="circle">
                <DirectionsBusIcon sx={{ fontSize: 16 }} />
            </div>, 
        value: "walk_transit"
    }, {
        html: 
            <div className="circle">
                <PedalBikeIcon sx={{ fontSize: 16 }} />
            </div>, 
        value: "bicycle"
    }, {
        html: 
            <div className="circle">
                <DirectionsWalkIcon sx={{ fontSize: 16 }} />
            </div>, 
        value: "foot"
    }
];

/**
 * Mapping of transport mode identifiers to timeline display icons
 */
export const timelineIcons: {[mode: string]: JSX.Element} = {
    foot:
        <div className="timeline-icon">
            <DirectionsWalkIcon sx={{ fontSize: 19 }} />
        </div>,
    bicycle:
        <div className="timeline-icon">
            <PedalBikeIcon sx={{ fontSize: 19 }} />
        </div>,
    rail: 
        <div className="timeline-icon">
            <TrainIcon sx={{ fontSize: 19 }} />
        </div>,
    bus:
        <div className="timeline-icon">
            <DirectionsBusIcon sx={{ fontSize: 19 }} />
        </div>,
    tram:
        <div className="timeline-icon">
            <TramIcon sx={{ fontSize: 19 }} />
        </div>,
    trolleybus:
        <div className="timeline-icon">
            <DirectionsBusIcon sx={{ fontSize: 19 }} />
        </div>,
    boat:
        <div className="timeline-icon">
            <DirectionsBoatIcon sx={{ fontSize: 19 }} />
        </div>,
    transfer:
        <div className="timeline-icon">
            <TransferWithinAStationIcon sx={{ fontSize: 17 }} />
        </div>,
    metro:
        <div className="timeline-icon">
            <DirectionsTransitIcon sx={{ fontSize: 19 }} />
        </div>,
};

/** End of file IconMappings.tsx */
