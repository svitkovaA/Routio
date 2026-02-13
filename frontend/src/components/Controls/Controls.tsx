/**
 * @file Controls.tsx
 * @brief Renders control elements for map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import LanguageSelect from "./Language/LanguageSelect";
import LayerSelect from "./Layer/LayerSelect";
import Information from "./Information/Information";
import './Controls.css'

type ControlsProps = {
    setShowInfo: (value: boolean) => void;
}

function Controls({
    setShowInfo
} : ControlsProps) {
    return (
        <div className="controls">
            <div className="controls-right">
                <LayerSelect />
                <LanguageSelect />
            </div>
            <Information
                setShowInfo={setShowInfo}
            />
        </div>
    );
}
export default Controls;

/** End of file Controls.tsx */
