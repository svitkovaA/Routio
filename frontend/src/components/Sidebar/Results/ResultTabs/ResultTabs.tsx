/**
 * @file ResultTabs.tsx
 * @brief Displays mode selection tabs for switching between trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import { MultimodalIcon } from "../../Planning/Icons/Icons";
import { useResult } from "../../../ResultContext";
import "./ResultTabs.css";
import { useRoute } from '../../../Routing/Route';

function ResultTabs() { 
    // Result context 
    const {
        setSelectedTripPatternIndex,
        resultActiveIndex ,setResultActiveIndex
    } = useResult();

    // User input context
    // const { setMode } = useInput();

    const route = useRoute();

    return (
        <div className="result-tabs" onClick={() => setSelectedTripPatternIndex(0)}>

            {/* Multimodal transport tab */}
            <div 
                className={"result-mode " + (resultActiveIndex === 0 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(0);
                    // setMode("transit,bicycle,walk"); 
                    route(0);
                }}
            >
                <MultimodalIcon iconSize={24}/>
            </div>

            {/* Public transport tab */}
            <div 
                className={"result-mode " + (resultActiveIndex === 1 ? "selected" : "")} 
                onClick={() => {
                    setResultActiveIndex(1);
                    // setMode("walk_transit");
                    route(1);
                }}
            >
                <div className="circle">
                    <DirectionsBusIcon />
                </div>
            </div>

            {/* Bicycle transport tab */}
            <div 
                className={"result-mode " + (resultActiveIndex === 2 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(2);
                    // setMode("bicycle");
                    route(2);
                }}
            >
                <div className="circle">
                    <PedalBikeIcon />
                </div>
            </div>

            {/* Walking transport tab */}
            <div 
                className={"result-mode " + (resultActiveIndex === 3 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(3);
                    // setMode("foot");
                    route(3);
                }}
            >
                <div className="circle">
                    <DirectionsWalkIcon />
                </div>
            </div>
        </div>
    );
}

export default ResultTabs;

/** End of file ResultTabs.tsx */
