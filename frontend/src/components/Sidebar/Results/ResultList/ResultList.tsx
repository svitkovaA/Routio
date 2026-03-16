/**
 * @file ResultList.tsx
 * @brief Displays the list of trip results based on the selected mode
 * @author Andrea Svitkova (xsvitka00)
 */

import ResultListItem from "./ResultListItem/ResultListItem";
import { useResult } from "../../../Contexts/ResultContext";
import Detail from "../Detail/Detail";

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
        <Detail
            tripPattern={pattern}
            recalculatePattern={recalculatePattern}
        />  
    );
}

export default ResultList;

/** End of file ResultList.tsx */
