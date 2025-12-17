import { useState } from "react";
import { API_BASE_URL } from "../config/config";
import { useResult } from "../ResultContext";

export function useRecalculatePattern() {
    const {
        result,
        selectedTripPatternIndex, 
        setResults,
        resultActiveIndex,
    } = useResult();

    const [publicLegIndex, setPublicLegIndex] = useState<number>(-1);

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
        const newResult = JSON.parse(JSON.stringify(result))
        newResult.tripPatterns[selectedTripPatternIndex] = newTripPattern;


        setResults(prev => 
            prev.map((originalResult, index) => 
                index === resultActiveIndex ? newResult : originalResult
        ));
        setPublicLegIndex(-1);
    }

    return { recalculatePattern, publicLegIndex, setPublicLegIndex };
}