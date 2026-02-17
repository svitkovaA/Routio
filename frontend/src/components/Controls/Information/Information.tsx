/**
 * @file Information.tsx
 * @brief Button component for opening the application information panel
 * @author Andrea Svitkova (xsvitka00)
 */

import InfoIcon from '@mui/icons-material/Info';
import { useTranslation } from 'react-i18next';
import CustomTooltip from '../../CustomTooltip/CustomTooltip';
import "./Information.css"

type InformationProps = {
    setShowInfo: (value: boolean) => void;  // Controls visibility of the information panel
}

function Information({
    setShowInfo
} : InformationProps) {
    // Translation function
    const { t } = useTranslation();

    return (
        <CustomTooltip title={t("tooltips.controls.info")}>
            <button 
                className={"controls-button controls-info"}
                onClick={() => setShowInfo(true)} 
                type="button"
                tabIndex={-1}
            >
                <InfoIcon sx={{ color: 'var(--color-text-primary)' }} />
            </button>
        </CustomTooltip>
    );
}

export default Information;

/** End of file Information.tsx */
