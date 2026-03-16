/**
 * @file useBackButtonClick.tsx
 * @brief Hook for handling back button navigation in the results view
 * @author Andrea Svitkova (xsvitka00)
 */

import { useCallback } from "react";
import { useResult } from "../../Contexts/ResultContext";

export function useBackButtonClick() {
    // Result context
    const {
        showDetail, setShowDetail,
        showDepartures,
        closeResults,
        setPublicLegIndex
    } = useResult();

    /**
     * Handles back navigation within the results view
     */
    const backButtonClick = useCallback(() => {
        if (showDetail) {
            // Close detail
            if (!showDepartures) {
                setShowDetail(false);
            }
            // Close other departures
            else {
                setPublicLegIndex(-1);
            }
        }
        // Close results
        else {
            closeResults();
        }
    }, [showDetail, showDepartures, closeResults, setShowDetail, setPublicLegIndex]);

    return { backButtonClick };
}

/** End of file useBackButtonClick.tsx */
