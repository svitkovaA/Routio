/**
 * @file ResultList.tsx
 * @brief Displays the list of trip results based on the selected mode
 * @author Andrea Svitkova (xsvitka00)
 */

import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ResultListItem from "./ResultListItem/ResultListItem";
import { useResult } from "../../../Contexts/ResultContext";
import Detail from "../Detail/Detail";
import { useTranslation } from 'react-i18next';
import "./ResultList.css";

type ResultListProps = {
    recalculatePattern: (selectedIndex: number, legIndex: number) => void;  // Function used to recalculate a trip pattern after selecting a different leg
}

function ResultList({
    recalculatePattern
} : ResultListProps) {
    // Result context
    const {
        result,
        selectedTripPatternIndex, setSelectedTripPatternIndex,
        setShowDetail,
        resultActiveIndex,
        pattern
    } = useResult();

    // Translation function
    const { t } = useTranslation();

    // Displays list of trip patterns for multimodal transport, public transport and shared bicycle
    if ([0,1].includes(resultActiveIndex) || (resultActiveIndex === 2 && result.tripPatterns.length > 1)) {
        return (
            <>
                {result.tripPatterns?.map((pattern, index) => (
                    <ResultListItem 
                        key={`${pattern.aimedEndTime}-${index}`}
                        pattern={pattern}
                        selected={index === selectedTripPatternIndex}
                        onClick={() => setSelectedTripPatternIndex(index)}
                        onClickDetail={() => setShowDetail(true)}
                    />
                ))}
            </>
        );
    }
    // If only one pattern is available display directly the detail view
    setSelectedTripPatternIndex(0);
    
    return (
        <>
            {(pattern.tooLongBikeDistance || pattern.tooLongWalkDistance) && (
                <div className="result-list-warning">
                    <WarningAmberIcon />
                    {t("resultsInfo.warningFootBicycle")}
                </div>
            )}
            <Detail
                recalculatePattern={recalculatePattern}
            />
        </>
    );
}

export default ResultList;

/** End of file ResultList.tsx */
