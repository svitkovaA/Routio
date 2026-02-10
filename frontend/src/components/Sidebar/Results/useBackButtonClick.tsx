import { useCallback } from "react";
import { useResult } from "../../ResultContext";

export function useBackButtonClick() {
    const {
        showDetail, setShowDetail,
        showDepartures,
        closeResults,
        setPublicLegIndex
    } = useResult();

    /**
     * Handle back navigation within the results view
     */
    const backButtonClick = useCallback(() => {
        if (showDetail) {
            if (!showDepartures) {
                setShowDetail(false);
            } else {
                setPublicLegIndex(-1);
            }
        }
        else {
            closeResults();
        }
    }, [showDetail, showDepartures, closeResults, setShowDetail, setPublicLegIndex]);

    return { backButtonClick };
}
