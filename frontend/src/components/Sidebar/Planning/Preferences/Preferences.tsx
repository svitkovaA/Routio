/**
 * @file Preferences.tsx
 * @brief Button component for opening advanced routing preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import TuneIcon from '@mui/icons-material/Tune';
import { useTranslation } from 'react-i18next';
import { useResult } from '../../../Contexts/ResultContext';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import "./Preferences.css";

function Preferences() {
    // Translation function
    const { t } = useTranslation();

    // Result context
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

/** End of file Preferences.tsx */
