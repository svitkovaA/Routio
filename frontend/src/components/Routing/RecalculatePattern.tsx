/**
 * @file RecalculatePattern.tsx
 * @brief Hook for recalculating a trip pattern
 * @author Andrea Svitkova (xsvitka00)
 */

import { API_BASE_URL } from "../config/config";
import { useResult } from "../Contexts/ResultContext";

/**
 * Hook handling trip pattern computation
 * 
 * @returns State related to pattern recalculation
 */
export function useRecalculatePattern() {
    // Result context
    const {
        result,
        selectedTripPatternIndex, 
        setResults,
        resultActiveIndex,
        publicLegIndex, setPublicLegIndex
    } = useResult();

    /**
     * Requests a recalculated trip pattern from the backend
     * 
     * @param selectedIndex Index of the selected alternative departure
     * @param legIndex Index of the leg
     */
    const recalculatePattern = async (selectedIndex: number, legIndex: number = publicLegIndex) => {
        const apiResult = await fetch(`${API_BASE_URL}/otherDepartures`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trip_pattern: result.tripPatterns[selectedTripPatternIndex],
                selected_index: selectedIndex,
                public_leg_index: legIndex
            })
        });

        const newTripPattern = await apiResult.json();

        // Create a copy of the active result
        const newResult = JSON.parse(JSON.stringify(result));
        newResult.tripPatterns[selectedTripPatternIndex] = newTripPattern;

        // Replace the active result with the recalculated one
        setResults(prev => 
            prev.map((originalResult, index) => 
                index === resultActiveIndex ? newResult : originalResult
        ));
        setPublicLegIndex(-1);
    }

    return { recalculatePattern };
}

/** End of file RecalculatePattern.tsx */
