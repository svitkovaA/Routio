/**
 * @file DetailSwitch.tsx
 * @brief Navigation for switching between trip pattern details
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import { IconButton } from "@mui/material";
import { useResult } from "../../../Contexts/ResultContext";
import { useTranslation } from 'react-i18next';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import "./DetailSwitch.css"

type DetailSwitchProps = {
    numOfPatterns: number;      // Total number of available trip patterns
};

function DetailSwitch({
    numOfPatterns,
}: DetailSwitchProps) {
    // Translation function
    const { t } = useTranslation();

    // Result context
    const {
        selectedTripPatternIndex,
        setSelectedTripPatternIndex
    } = useResult();

    return (
        <div className="detail-switch">

            {/* Navigation to the previous trip pattern */}
            <CustomTooltip title={t("tooltips.detail.detailPreview.previousRoute")}>
                <IconButton
                    className="detail-switch-arrow"
                    onClick={() => {
                        setSelectedTripPatternIndex((prev) =>
                            prev > 0 ? prev - 1 : numOfPatterns - 1
                        );
                    }}
                >
                    <KeyboardArrowLeftIcon />
                </IconButton>
            </CustomTooltip>

            {/* Dots for direct pattern selection */}
            <CustomTooltip title={t("tooltips.detail.detailPreview.otherRouteDots")}>
                <div className="dots">
                    {Array.from({ length: numOfPatterns }, (_, i) => (
                        <IconButton
                            className="dots-button"
                            key={i} 
                            onClick={() => setSelectedTripPatternIndex(i)}
                        >
                            {i === selectedTripPatternIndex ? (
                                <RadioButtonCheckedIcon className="dot"/>
                            ) : (
                                <RadioButtonUncheckedIcon className="dot"/>
                            )}
                        </IconButton>
                    ))}
                </div>
            </CustomTooltip>

            {/* Navigation to the next trip pattern */}
            <CustomTooltip title={t("tooltips.detail.detailPreview.nextRoute")}>
                <IconButton
                    className="detail-switch-arrow"
                    onClick={() => {
                        setSelectedTripPatternIndex((prev) =>
                            prev < numOfPatterns - 1 ? prev + 1 : 0
                        );
                    }}
                >
                    <KeyboardArrowRightIcon />
                </IconButton>
            </CustomTooltip>
        </div>
    );
}

export default DetailSwitch;

/** End of file DetailSwitch.tsx */
