/**
 * @file ResultList.tsx
 * @brief Displays the list of trip results based on the selected mode
 * @author Andrea Svitkova (xsvitka00)
 */

import Bicycle from "./Bicycle/Bicycle";
import Foot from "./Walk/Walk";
import ResultListItem from "./ResultListItem/ResultListItem";
import { Mode, ResultsType } from "../../../types/types";

type ResultListProps = {
    result: ResultsType;
    mode: Mode | undefined;
    selectedTripPatternIndex: number;
    setSelectedTripPatternIndex: (index: number) => void;
    showDetail: boolean;
    setShowDetail: (value: boolean) => void;
}

function ResultList({
    result,
    mode,
    selectedTripPatternIndex,
    setSelectedTripPatternIndex,
    showDetail,
    setShowDetail
} : ResultListProps) {
    if (!mode) return null;
    if (mode === "transit,bicycle,walk" || mode === "walk_transit" || (mode === "bicycle" && result.tripPatterns.length > 1)) {
        return (
            <>
                {result.tripPatterns?.map((pattern, index) => (
                    <ResultListItem 
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
                <Bicycle
                    result={result}
                    selectedTripPatternIndex={selectedTripPatternIndex}
                    setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                />
            ) : (
                <Foot
                    result={result}
                    selectedTripPatternIndex={selectedTripPatternIndex}
                    setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                />
            )}
        </>
    );
}

export default ResultList;

/** End of file ResultList.tsx */
