/**
 * @file ResultList.tsx
 * @brief Displays the list of trip results based on the selected mode
 * @author Andrea Svitkova (xsvitka00)
 */

import Bicycle from "./Bicycle/Bicycle";
import Foot from "./Walk/Walk";
import ResultListItem from "./ResultListItem/ResultListItem";
import { useInput } from "../../../InputContext";
import { useResult } from "../../../ResultContext";

function ResultList() {
    const {
        result,
        selectedTripPatternIndex, setSelectedTripPatternIndex,
        setShowDetail
    } = useResult();
    const { mode } = useInput();

    if (!mode) 
        return null;
    
    if (mode === "transit,bicycle,walk" || mode === "walk_transit" || (mode === "bicycle" && result.tripPatterns.length > 1)) {
        return (
            <>
                {result.tripPatterns?.map((pattern, index) => (
                    <ResultListItem 
                        key={`${index}`}
                        pattern={pattern}
                        selected={index === selectedTripPatternIndex}
                        onClick={() => setSelectedTripPatternIndex(index)}
                        onClickDetail={() => setShowDetail(true)}
                    />
                ))}
            </>
        );
    }
    return (
        <>
            {mode === "bicycle" ? (
                <Bicycle />
            ) : (
                <Foot />
            )}
        </>
    );
}

export default ResultList;

/** End of file ResultList.tsx */
