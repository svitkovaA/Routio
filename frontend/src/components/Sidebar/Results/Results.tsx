/**
 * @file Results.tsx
 * @brief Displays routing results and trip details
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import { useTranslation } from "react-i18next";
import ResultTabs from "./ResultTabs/ResultTabs";
import ResultList from "./ResultList/ResultList";
import ResultListItem from "./ResultList/ResultListItem/ResultListItem";
import DetailSwitch from "./DetailSwitch/DetailSwitch";
import Detail from "./Detail/Detail";
import MoreDepartures from "./MoreDepartures/MoreDepartures";
import { useResult } from "../../ResultContext";
import { useRecalculatePattern } from "../../Routing/RecalculatePattern";
import "./Results.css";

type ResultsProps = {
    closeResults: () => void;
};

function Results({ closeResults } : ResultsProps) {
    const { t } = useTranslation();

    // Results context
    const {
        showDetail, setShowDetail,
        showDepartures,
        result,
        resultActiveIndex,
        pattern
    } = useResult();

    // Hook for recalculating trip pattern
    const { recalculatePattern, publicLegIndex, setPublicLegIndex } = useRecalculatePattern();

    // Description of the routing modes
    const descriptions: String[] = [
        t("modeDescriptions.multimodalTransport") as String,
        t("modeDescriptions.publicTransport") as String,
        t("modeDescriptions.bicycle") as String,
        t("modeDescriptions.walk") as String
    ]

    /**
     * Handle back navigation within the results view
     */
    const handleBackButtonClick = () => {
        if (showDetail) {
            setPublicLegIndex(-1);
            if (!showDepartures) {
                setShowDetail(false);
            }
        }
        else {
            closeResults();
        }
    };

    return (
        <div className="results">
            {/* Results header */}
            <div className="sidebar-header">
                <button className="back-button" onClick={handleBackButtonClick}>
                    <KeyboardArrowLeftIcon fontSize="large" />
                </button>
                <span onClick={handleBackButtonClick}>{showDetail ? showDepartures ? "Other departures" : "Details" : t("results")}</span>

                {/* Header content depends on current view */}
                {!showDetail ? (
                    <>
                        {/* Tabs for switching routing modes */}
                        <ResultTabs 
                        />

                        {/* Description of the selected routing mode */}
                        <div className="description selected">
                            {descriptions[resultActiveIndex]}
                        </div>
                    </>
                ) : (
                    <>
                        {!showDepartures && (
                            <div className="detail-header">
        
                                {/* Summary of selected trip pattern */}
                                <ResultListItem
                                    pattern={pattern}
                                />
        
                                {/* Trip details */}
                                <DetailSwitch
                                    numOfPatterns={result.tripPatterns.length}
                                    setPublicLegIndex={setPublicLegIndex}
                                />
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Results content */}
            <div className="results-content">
                {result?.tripPatterns?.length === 0 ? (
                    <>No results found</>
                ) : !showDetail ? (
                    // List of available trip patterns
                    <ResultList />
                ) : showDepartures ? (
                    // Alternative departures for a selected public transport
                    <MoreDepartures
                        leg={pattern.originalLegs[publicLegIndex]}  
                        recalculatePattern={recalculatePattern}               
                    />
                ) : (
                    // Detailed view of the selected trip pattern
                    <Detail
                        tripPattern={pattern}
                        setPublicLegIndex={setPublicLegIndex}
                        recalculatePattern={recalculatePattern}
                    />
                )}
            </div>
        </div>
    );
}
export default Results;

/** End of file Results.tsx */
