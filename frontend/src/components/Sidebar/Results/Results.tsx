/**
 * @file Results.tsx
 * @brief Displays routing results and trip details
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useTranslation } from "react-i18next";
import ResultTabs from "./ResultTabs/ResultTabs";
import ResultList from "./ResultList/ResultList";
import ResultListItem from "./ResultList/ResultListItem/ResultListItem";
import DetailSwitch from "./DetailSwitch/DetailSwitch";
import Detail from "./Detail/Detail";
import MoreDepartures from "./MoreDepartures/MoreDepartures";
import { useResult } from "../../Contexts/ResultContext";
import { useRecalculatePattern } from "../../Routing/RecalculatePattern";
import { useBackButtonClick } from './useBackButtonClick';
import ResultLoading from './ResultLoading/ResultLoading';
import "./Results.css";

function Results() {
    // Translation function
    const { t } = useTranslation();

    // Results context
    const {
        showDetail,
        showDepartures,
        result,
        resultActiveIndex,
        pattern,
        publicLegIndex,
        loading,
        routingError
    } = useResult();

    // Hook for recalculating trip pattern
    const { recalculatePattern } = useRecalculatePattern();

    // Hook for back button click
    const { backButtonClick } = useBackButtonClick();

    // Description of the routing modes
    const descriptions: string[] = [
        t("modeDescriptions.multimodalTransport") as string,
        t("modeDescriptions.publicTransport") as string,
        t("modeDescriptions.bicycle") as string,
        t("modeDescriptions.walk") as string
    ];

    return (
        <div className="results">
            {/* Results header */}
            <div className="sidebar-header">
                <button className="back-button" onClick={backButtonClick}>
                    <KeyboardArrowLeftIcon fontSize="large" />
                </button>
                <span onClick={backButtonClick}>{showDetail ? showDepartures ? t("detailInfo.publicTransport.otherDepartures") : t("detail") : t("results")}</span>

                {/* Header content depends on current view */}
                {!showDetail ? (
                    <>
                        {/* Tabs for switching routing modes */}
                        <ResultTabs />

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
                                <ResultListItem pattern={pattern} />
        
                                {/* Trip details */}
                                <DetailSwitch numOfPatterns={result.tripPatterns.length}/>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Results content */}
            <div className="results-content">
                {loading ? (
                    <ResultLoading />
                ) : routingError ? (
                    <div className="routing-error">
                        <WarningAmberIcon />
                        {t("resultsInfo.routingError")}
                    </div>
                ) : result?.tripPatterns?.length === 0 ? (
                    <div className="no-results">
                        <WarningAmberIcon />
                        {t("resultsInfo.noResults")}
                    </div>
                ) : !showDetail ? (
                    // List of available trip patterns
                    <ResultList
                        recalculatePattern={recalculatePattern}
                    />
                ) : showDepartures ? (
                    // Alternative departures for a selected public transport
                    <MoreDepartures
                        leg={pattern?.originalLegs[publicLegIndex]}  
                        recalculatePattern={recalculatePattern}               
                    />
                ) : (
                    // Detailed view of the selected trip pattern
                    <Detail
                        recalculatePattern={recalculatePattern}
                    />
                )}
            </div>
        </div>
    );
}
export default Results;

/** End of file Results.tsx */
