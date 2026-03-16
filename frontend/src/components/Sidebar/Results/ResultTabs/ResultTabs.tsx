/**
 * @file ResultTabs.tsx
 * @brief Displays mode selection tabs for switching between trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import PedalBikeIcon from '@mui/icons-material/PedalBike';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import { MultimodalIcon } from "../../Planning/Icons/Icons";
import { useResult } from "../../../Contexts/ResultContext";
import { useRoute } from '../../../Routing/Route';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import { useTranslation } from 'react-i18next';
import "./ResultTabs.css";

function ResultTabs() {
    // Translation function
    const { t } = useTranslation();

    // Result context 
    const {
        setSelectedTripPatternIndex,
        resultActiveIndex ,setResultActiveIndex
    } = useResult();

    // Hook for triggering route computation
    const route = useRoute();

    return (
        <div className="result-tabs" onClick={() => setSelectedTripPatternIndex(0)}>

            {/* Multimodal transport tab */}
            <CustomTooltip title={t("tooltips.results.resultTabs.multimodal")}>
                <div 
                    className={"result-mode " + (resultActiveIndex === 0 ? "selected" : "")}
                    onClick={() => {
                        setResultActiveIndex(0);
                        route(0);
                    }}
                >
                    <MultimodalIcon iconSize={24}/>
                </div>
            </CustomTooltip>

            {/* Public transport tab */}
            <CustomTooltip title={t("tooltips.results.resultTabs.publicTransport")}>
                <div 
                    className={"result-mode " + (resultActiveIndex === 1 ? "selected" : "")} 
                    onClick={() => {
                        setResultActiveIndex(1);
                        route(1);
                    }}
                >
                    <div className="circle">
                        <DirectionsBusIcon />
                    </div>
                </div>
            </CustomTooltip>

            {/* Bicycle tab */}
            <CustomTooltip title={t("tooltips.results.resultTabs.bicycle")}>
                <div 
                    className={"result-mode " + (resultActiveIndex === 2 ? "selected" : "")}
                    onClick={() => {
                        setResultActiveIndex(2);
                        route(2);
                    }}
                >
                    <div className="circle">
                        <PedalBikeIcon />
                    </div>
                </div>
            </CustomTooltip>

            {/* Walking tab */}
            <CustomTooltip title={t("tooltips.results.resultTabs.foot")}>
                <div 
                    className={"result-mode " + (resultActiveIndex === 3 ? "selected" : "")}
                    onClick={() => {
                        setResultActiveIndex(3);
                        route(3);
                    }}
                >
                    <div className="circle">
                        <DirectionsWalkIcon />
                    </div>
                </div>
            </CustomTooltip>
        </div>
    );
}

export default ResultTabs;

/** End of file ResultTabs.tsx */
