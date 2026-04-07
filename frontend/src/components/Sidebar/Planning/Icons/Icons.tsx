/**
 * @file Icons.tsx
 * @brief Provides icons for transport modes and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
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

/** End of file Icons.tsx */
