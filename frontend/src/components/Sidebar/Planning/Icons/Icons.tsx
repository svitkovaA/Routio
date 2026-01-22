/**
 * @file Icons.tsx
 * @brief Provides icons for transport modes, multimodal trips, accuracy indicators, and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import TrainIcon from '@mui/icons-material/Train';
import TramIcon from '@mui/icons-material/Tram';
import DirectionsBoatIcon from '@mui/icons-material/DirectionsBoat';
import { JSX } from "react";
import { Mode } from "../../../types/types";
import "./Icons.css";

export function MultimodalIcon() {
    return (
        <div className="multimodal-icon">
            <div className="circle public-transport">
                <DirectionsBusIcon sx={{ fontSize: 16 }} />
            </div>
            <div className="circle bicycle">
                <PedalBikeIcon sx={{ fontSize: 16 }} />
            </div>
            <div className="circle walk">
                <DirectionsWalkIcon sx={{ fontSize: 16 }} />
            </div>
        </div>
    );
}

export const modeIcons: {html: JSX.Element, value: Mode}[] = [{
        html: <MultimodalIcon />, 
        value: "transit,bicycle,walk"
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

export const timelineIcons: {[mode: string]: JSX.Element} = {
    foot:
        <div className="timeline-icon">
            <DirectionsWalkIcon fontSize="small" />
        </div>,
    bicycle:
        <div className="timeline-icon">
            <PedalBikeIcon fontSize="small" />
        </div>,
    rail: 
        <div className="timeline-icon">
            <TrainIcon fontSize="small" />
        </div>,
    bus:
        <div className="timeline-icon">
            <DirectionsBusIcon fontSize="small" />
        </div>,
    tram:
        <div className="timeline-icon">
            <TramIcon fontSize="small" />
        </div>,
    trolleybus:
        <div className="timeline-icon">
            <DirectionsBusIcon fontSize="small" />
        </div>,
    boat:
        <div className="timeline-icon">
            <DirectionsBoatIcon fontSize="small" />
        </div>
}

/** End of file Icons.tsx */
