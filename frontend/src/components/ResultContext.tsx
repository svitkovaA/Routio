/**
 * @file ResultContext.tsx
 * @brief 
 * @author Andrea Svitkova (xsvitka00)
 */

import React, { createContext, useContext, useMemo, useState } from "react"
import { ResultsType, TripPattern } from "./types/types";

type ResultContextType = {
    pattern: TripPattern;
    result: ResultsType;
    results: ResultsType[];
    setResults: (value: ResultsType[] | ((prev: ResultsType[]) => ResultsType[])) => void;
    resultActiveIndex: number;
    setResultActiveIndex: (value: number) => void;
    selectedTripPatternIndex: number;
    setSelectedTripPatternIndex: (value: number | ((prev: number) => number)) => void;
    showResults: boolean;
    setShowResults: (value: boolean) => void;
    showDetail: boolean;
    setShowDetail: (value: boolean) => void;
};

const ResultContext = createContext<ResultContextType | undefined>(undefined);

export function ResultProvider({ children } : {children: React.ReactNode}) {

    const [results, setResults] = useState<ResultsType[]>(Array(4).fill({tripPatterns: [], active: false}));
    const [resultActiveIndex, setResultActiveIndex] = useState<number>(-1);
    const [selectedTripPatternIndex, setSelectedTripPatternIndex] = useState<number>(0);
    const [showResults, setShowResults] = useState(false);
    const [showDetail, setShowDetail] = useState<boolean>(false);

    const value = useMemo(() => ({
        pattern: results[resultActiveIndex]?.tripPatterns[selectedTripPatternIndex],
        result: results[resultActiveIndex],
        results, setResults,
        resultActiveIndex, setResultActiveIndex,
        selectedTripPatternIndex, setSelectedTripPatternIndex,
        showResults, setShowResults,
        showDetail, setShowDetail
    }), [
        results,
        resultActiveIndex,
        selectedTripPatternIndex,
        showResults,
        showDetail
    ]);
    
    return <ResultContext.Provider value={value}>{children}</ResultContext.Provider>;
}

export function useResult() {
    const ctx = useContext(ResultContext);
    if (!ctx) {
        throw new Error("useResult must be used within ResultProvider");
    }
    return ctx;
}

/** End of file ResultContext.tsx */
