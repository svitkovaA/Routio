/**
 * @file InfoSettings.tsx
 * @brief Display buttons for settings and information in the sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import { useResult } from '../../../ResultContext';
import "./InfoSettings.css";

type InfoSettingsProps = {
    showInfo: () => void;
};

function InfoSettings({ showInfo }: InfoSettingsProps) {
    const { setShowSettings } = useResult();
    return (
        <div className="grid-wrapper">
            <button 
                className="input-wrapper" 
                onClick={() => setShowSettings(true)} 
                type="button"
                tabIndex={-1}
            >
                <SettingsIcon sx={{ color: 'var(--color-icons)' }} />
            </button>
            <button 
                className="input-wrapper" 
                onClick={showInfo} 
                type="button"
                tabIndex={-1}
            >
                <InfoIcon sx={{ color: 'var(--color-icons)' }} />
            </button>
        </div>
    );
}

export default InfoSettings;

/** End of file InfoSettings.tsx */
