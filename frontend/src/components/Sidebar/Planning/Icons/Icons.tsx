/**
 * @file Icons.tsx
 * @brief Provides icons for transport modes and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import { JSX } from "react";
import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import TrainIcon from '@mui/icons-material/Train';
import TramIcon from '@mui/icons-material/Tram';
import DirectionsBoatIcon from '@mui/icons-material/DirectionsBoat';
import TransferWithinAStationIcon from '@mui/icons-material/TransferWithinAStation';
import { Mode } from "../../../types/types";
import "./Icons.css";

type MultimodalIconProps = {
    iconSize?: number;      // Optional icon size
};

/**
 * Renders a combined icon representing a multimodal trip
 * 
 * @param iconSize Optional icon size
 */
export function MultimodalIcon({
    iconSize = 16
} : MultimodalIconProps) {
    return (
        <div className="multimodal-icon">
            <div className="circle public-transport">
                <DirectionsBusIcon sx={{ fontSize: iconSize }} />
            </div>
            <div className="circle bicycle">
                <PedalBikeIcon sx={{ fontSize: iconSize }} />
            </div>
            <div className="circle walk">
                <DirectionsWalkIcon sx={{ fontSize: iconSize }} />
            </div>
        </div>
    );
}

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
]

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
        </div>
}

/** End of file Icons.tsx */
