/**
 * @file DetailSwitch.tsx
 * @brief Provides navigation between trip pattern details
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import { IconButton } from "@mui/material";
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import "./DetailSwitch.css"
import { useResult } from "../../../ResultContext";

type DetailSwitchProps = {
    numOfPatterns: number;
    setPublicLegIndex: (value: number) => void;
};

function DetailSwitch({
    numOfPatterns,
    setPublicLegIndex
}: DetailSwitchProps) {
    const { selectedTripPatternIndex, setSelectedTripPatternIndex } = useResult();

    return (
        <div className="detail-switch">
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
