/**
 * @file InfoSettings.tsx
 * @brief Display buttons for settings and information in the sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import TuneIcon from '@mui/icons-material/Tune';
import { useResult } from '../../../ResultContext';
import "./Preferences.css";

function Preferences() {
    const { setShowSettings } = useResult();
    return (
        <button 
            className="input-wrapper preferences-button" 
            onClick={() => setShowSettings(true)} 
            type="button"
            tabIndex={-1}
        >
            <TuneIcon sx={{ color: 'var(--color-icons)' }} />
        </button>
    );
}

export default Preferences;

/** End of file InfoSettings.tsx */
