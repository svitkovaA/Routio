/**
 * @file InfoSettings.tsx
 * @brief Display buttons for settings and information in the sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import "./InfoSettings.css";

type InfoSettingsProps = {
    showSettings: () => void;
    showInfo: () => void;
};

function InfoSettings({ showSettings, showInfo }: InfoSettingsProps) {
    return (
        <div className="grid-wrapper">
            <button 
                className="input-wrapper" 
                onClick={showSettings} 
                type="button"
            >
                <SettingsIcon sx={{ color: 'var(--color-icons)' }} />
            </button>
            <button 
                className="input-wrapper" 
                onClick={showInfo} 
                type="button"
            >
                <InfoIcon sx={{ color: 'var(--color-icons)' }} />
            </button>
        </div>
    );
}

export default InfoSettings;

/** End of file InfoSettings.tsx */
