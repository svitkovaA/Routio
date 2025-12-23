/**
 * @file Results.tsx
 * @brief Displays trip search results
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
import "./Results.css";
import { useRecalculatePattern } from "../../Routing/RecalculatePattern";

type ResultsProps = {
    closeResults: () => void;
};

function Results({ closeResults } : ResultsProps) {
    const {
        showDetail, setShowDetail,
        result,
        resultActiveIndex,
        pattern
    } = useResult();

    const { t } = useTranslation();
    const { recalculatePattern, publicLegIndex, setPublicLegIndex } = useRecalculatePattern();
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

    return (
        <div className="results">
            <div className="sidebar-header">
                <button className="back-button" onClick={handleBackButtonClick}>
                    <KeyboardArrowLeftIcon fontSize="large" />
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
                )}
            </div>
        </div>
    );
}
export default Results;

/** End of file Results.tsx */
