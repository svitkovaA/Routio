/**
 * @file Controls.tsx
 * @brief Renders control elements for map interaction
 * @author Andrea Svitkova (xsvitka00)
 */

import LanguageSelect from "./Language/LanguageSelect";
import LayerSelect from "./Layer/LayerSelect";
import './Controls.css'

type ControlsProps = {
    showInfo: boolean;      // State whether the information is currently visible
    closeInfo: () => void;  // Callback function used to close the information panel
}

function Controls({
    showInfo,
    closeInfo
} : ControlsProps) {
    return (
        <div className="controls">
            <LayerSelect
                showInfo={showInfo}
                closeInfo={closeInfo}
            />
            <LanguageSelect 
                showInfo={showInfo}
                closeInfo={closeInfo}
            />
        </div>
    );
}
export default Controls;

/** End of file Controls.tsx */
