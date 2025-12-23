/**
 * @file Icons.tsx
 * @brief Provides icons for transport modes, multimodal trips, accuracy indicators, and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import GpsFixedIcon from '@mui/icons-material/GpsFixed';
import CircleIcon from '@mui/icons-material/Circle';
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
                <DirectionsBusIcon fontSize="small" />
            </div>
            <div className="circle bicycle">
                <PedalBikeIcon fontSize="small" />
            </div>
            <div className="circle walk">
                <DirectionsWalkIcon fontSize="small" />
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
                <DirectionsBusIcon />
            </div>, 
        value: "walk_transit"
    }, {
        html: 
            <div className="circle">
                <PedalBikeIcon />
            </div>, 
        value: "bicycle"
    }, {
        html: 
            <div className="circle">
                <DirectionsWalkIcon />
            </div>, 
        value: "foot"
    }
]

export const accuracyIcons: {html: JSX.Element, exact: boolean}[] = [{
        html: 
            <div className="accuracy-icon">
                <GpsFixedIcon className="accuracy" />
            </div>, 
        exact: true
    }, {
        html: 
            <div className="accuracy-icon">
                <CircleIcon className="accuracy" />
            </div>, 
        exact: false
    }
]

export const timelineIcons: {[mode: string]: JSX.Element} = {
    foot:
        <div className="timeline-icon">
            <DirectionsWalkIcon />
        </div>,
    bicycle:
        <div className="timeline-icon">
            <PedalBikeIcon />
        </div>,
    rail: 
        <div className="timeline-icon">
            <TrainIcon />
        </div>,
    bus:
        <div className="timeline-icon">
            <DirectionsBusIcon />
        </div>,
    tram:
        <div className="timeline-icon">
            <TramIcon />
        </div>,
    trolleybus:
        <div className="timeline-icon">
            <DirectionsBusIcon />
        </div>,
    boat:
        <div className="timeline-icon">
            <DirectionsBoatIcon />
        </div>
}

/** End of file Icons.tsx */
