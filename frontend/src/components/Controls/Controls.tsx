/**
 * @file Controls.tsx
 * @brief Renders control elements including layer selection, language selection and information panel
 * @author Andrea Svitkova (xsvitka00)
 */

import LayerSelect from "./Layer/LayerSelect";
import LanguageSelect from "./Language/LanguageSelect";
import Information from "./Information/Information";
import './Controls.css'

type ControlsProps = {
    setShowInfo: (value: boolean) => void;  // Controls visibility of the information panel
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
