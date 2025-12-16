/**
 * @file Results.tsx
 * @brief Displays trip search results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import { Mode, ResultsType, Waypoint } from "../../types/types";
import ResultTabs from "./ResultTabs/ResultTabs";
import ResultList from "./ResultList/ResultList";
import ResultListItem from "./ResultList/ResultListItem/ResultListItem";
import DetailSwitch from "./DetailSwitch/DetailSwitch";
import Detail from "./Detail/Detail";
import MoreDepartures from "./MoreDepartures/MoreDepartures";
import "./Results.css";
import { API_BASE_URL } from "../../config/config";

type ResultsProps = {
    closeResults: () => void;
    mode: Mode | undefined;
    setMode: (value: Mode| undefined) => void;
    result: ResultsType;
    setResults: (value: ResultsType[] | ((prev: ResultsType[]) => ResultsType[])) => void;
    resultActiveIndex: number;
    setResultActiveIndex: (value: number) => void;
    selectedTripPatternIndex: number;
    setSelectedTripPatternIndex: (value: number | ((prev: number) => number)) => void;
    showDetail: boolean;
    setShowDetail: (value: boolean) => void;
    waypoints: Waypoint[];
    style?: React.CSSProperties;
};

function Results({ 
    closeResults,
    mode,
    setMode,
    result,
    setResults,
    resultActiveIndex,
    setResultActiveIndex,
    selectedTripPatternIndex,
    setSelectedTripPatternIndex,
    showDetail,
    setShowDetail,
    waypoints,
    style 
} : ResultsProps) {
    const { t } = useTranslation();
    const [publicLegIndex, setPublicLegIndex] = useState<number>(-1)
    const descriptions: String[] = [
        t("modeDescriptions.multimodalTransport") as String,
        t("modeDescriptions.publicTransport") as String,
        t("modeDescriptions.bicycle") as String,
        t("modeDescriptions.walk") as String
    ]
    const handleBackButtonClick = () => {
        if (showDetail) {
            setShowDetail(false);
            setPublicLegIndex(-1);
        }
        else {
            closeResults();
        }
    };

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

    return (
        <div className="results" style={style}>
            <div className="sidebar-header">
                <button className="back-button" onClick={handleBackButtonClick}>
                    <FontAwesomeIcon icon={faAngleLeft} />
                </button>
                <span onClick={handleBackButtonClick}>{showDetail ? "Details" : t("results")}</span>
                {/* <Refresh /> */}
                {!showDetail ? (
                    <>
                        <ResultTabs 
                            resultActiveIndex={resultActiveIndex}
                            setResultActiveIndex={setResultActiveIndex}
                            setMode={setMode}
                            setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                        />
                        <div className="description selected">
                            {descriptions[resultActiveIndex]}
                        </div>
                    </>
                ) : (
                    <div className="detail-header">
                        <ResultListItem
                            pattern={result.tripPatterns[selectedTripPatternIndex]}
                        />
                        <DetailSwitch
                            numOfPatterns={result.tripPatterns.length}
                            selectedTripPatternIndex={selectedTripPatternIndex}
                            setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                            setPublicLegIndex={setPublicLegIndex}
                        />
                    </div>
                )}
            </div>

            <div className="results-content">
                {result?.tripPatterns?.length === 0 ? (
                    <>No results found</>
                ) : !showDetail ? (
                    <ResultList
                        result={result}
                        mode={mode}
                        selectedTripPatternIndex={selectedTripPatternIndex}
                        setSelectedTripPatternIndex={setSelectedTripPatternIndex}
                        showDetail={showDetail}
                        setShowDetail={setShowDetail}
                    />
                ) : publicLegIndex !== -1 ? (
                    <MoreDepartures
                        leg={result.tripPatterns[selectedTripPatternIndex].originalLegs[publicLegIndex]}  
                        recalculatePattern={recalculatePattern}               
                    />
                ) : (
                    <Detail
                        tripPattern={result.tripPatterns[selectedTripPatternIndex]}
                        waypoints={waypoints}
                        setPublicLegIndex={setPublicLegIndex}
                        recalculatePattern={recalculatePattern}
                    />
                    )
                }
            </div>
        </div>
    );
}
export default Results;

/** End of file Results.tsx */
