/**
 * @file Results.tsx
 * @brief Displays trip search results
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import ResultTabs from "./ResultTabs/ResultTabs";
import ResultList from "./ResultList/ResultList";
import ResultListItem from "./ResultList/ResultListItem/ResultListItem";
import DetailSwitch from "./DetailSwitch/DetailSwitch";
import Detail from "./Detail/Detail";
import MoreDepartures from "./MoreDepartures/MoreDepartures";
import { API_BASE_URL } from "../../config/config";
import { useResult } from "../../ResultContext";
import "./Results.css";

type ResultsProps = {
    closeResults: () => void;
};

function Results({ closeResults } : ResultsProps) {
    const {
        showDetail, setShowDetail,
        result,
        selectedTripPatternIndex, 
        setResults,
        resultActiveIndex,
        pattern
    } = useResult();

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
        <div className="results">
            <div className="sidebar-header">
                <button className="back-button" onClick={handleBackButtonClick}>
                    <FontAwesomeIcon icon={faAngleLeft} />
                </button>
                <span onClick={handleBackButtonClick}>{showDetail ? "Details" : t("results")}</span>
                {!showDetail ? (
                    <>
                        <ResultTabs 
                        />
                        <div className="description selected">
                            {descriptions[resultActiveIndex]}
                        </div>
                    </>
                ) : (
                    <div className="detail-header">
                        <ResultListItem
                            pattern={pattern}
                        />
                        <DetailSwitch
                            numOfPatterns={result.tripPatterns.length}
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
                    />
                ) : publicLegIndex !== -1 ? (
                    <MoreDepartures
                        leg={pattern.originalLegs[publicLegIndex]}  
                        recalculatePattern={recalculatePattern}               
                    />
                ) : (
                    <Detail
                        tripPattern={pattern}
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
