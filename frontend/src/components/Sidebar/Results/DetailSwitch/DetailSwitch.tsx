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
import { useResult } from "../../../ResultContext";
import "./DetailSwitch.css"

type DetailSwitchProps = {
    numOfPatterns: number;                          // Total number of available trip patterns
    setPublicLegIndex: (value: number) => void;     // Setter used to reset selected leg
};

function DetailSwitch({
    numOfPatterns,
    setPublicLegIndex
}: DetailSwitchProps) {
    // Result context
    const { selectedTripPatternIndex, setSelectedTripPatternIndex } = useResult();

    return (
        <div className="detail-switch">

            {/* Navigation to the previous trip pattern */}
            <IconButton
                className="detail-switch-arrow"
                onClick={() => {
                    setSelectedTripPatternIndex((prev) =>
                        prev > 0 ? prev - 1 : numOfPatterns - 1
                    );
                    setPublicLegIndex(-1);
                }}
            >
                <KeyboardArrowLeftIcon />
            </IconButton>

            {/* Dots for direct pattern selection */}
            <div className="dots">
                {Array.from({ length: numOfPatterns }, (_, i) => (
                <IconButton 
                    key={i} 
                    onClick={() => {
                        setSelectedTripPatternIndex(i); 
                        setPublicLegIndex(-1);
                    }}
                >
                    {i === selectedTripPatternIndex ? (
                        <RadioButtonCheckedIcon className="dot"/>
                    ) : (
                        <RadioButtonUncheckedIcon className="dot"/>
                    )}
                </IconButton>
                ))}
            </div>

            {/* Navigation to the next trip pattern */}
            <IconButton
                className="detail-switch-arrow"
                onClick={() => {
                    setSelectedTripPatternIndex((prev) =>
                        prev < numOfPatterns - 1 ? prev + 1 : 0
                    );
                    setPublicLegIndex(-1);
                }}
            >
                <KeyboardArrowRightIcon />
            </IconButton>
        </div>
    );
}

export default DetailSwitch;

/** End of file DetailSwitch.tsx */
