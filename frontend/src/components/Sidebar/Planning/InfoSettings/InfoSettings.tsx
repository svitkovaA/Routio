/**
 * @file InfoSettings.tsx
 * @brief Display buttons for settings and information in the sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faGear, faCircleInfo } from '@fortawesome/free-solid-svg-icons';
import "./InfoSettings.css";

type InfoSettingsProps = {
    showSettings: () => void;
    showInfo: () => void;
};

function InfoSettings({ showSettings, showInfo }: InfoSettingsProps) {
    return (
    <div className="grid-wrapper">
        <button className="input-wrapper" onClick={showSettings} type="button">
            <FontAwesomeIcon icon={faGear} />
        </button>
        <button className="input-wrapper" onClick={showInfo} type="button">
            <FontAwesomeIcon icon={faCircleInfo} />
        </button>
    </div>
    );
}

export default InfoSettings;

/** End of file InfoSettings.tsx */
