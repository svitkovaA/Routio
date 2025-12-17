/**
 * @file Controls.tsx
 * @brief Displays rendered map controls
 * @author Andrea Svitkova (xsvitka00)
 */

import LanguageSelect from "./Language/LanguageSelect";
import LayerSelect from "./Layer/LayerSelect";
import './Controls.css'

type ControlsProps = {
    showInfo: boolean;
    closeInfo: () => void;
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
