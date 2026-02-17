/**
 * @file InfoSettings.tsx
 * @brief Display buttons for settings and information in the sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import TuneIcon from '@mui/icons-material/Tune';
import { useTranslation } from 'react-i18next';
import { useResult } from '../../../ResultContext';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import "./Preferences.css";

function Preferences() {
    const { t } = useTranslation();
    const { setShowSettings } = useResult();

    return (
        <CustomTooltip title={t("tooltips.inputForm.preferencesButton")}>
            <button 
                className="input-wrapper preferences-button" 
                onClick={() => setShowSettings(true)} 
                type="button"
                tabIndex={-1}
            >
            <TuneIcon sx={{ color: 'var(--color-icons)' }} />
        </button>
        </CustomTooltip>
    );
}

export default Preferences;

/** End of file InfoSettings.tsx */
