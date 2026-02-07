import { useResult } from "../../ResultContext";
import { useRecalculatePattern } from "../../Routing/RecalculatePattern";

export function useBackButtonClick() {
    const {
        showDetail, setShowDetail,
        showDepartures,
        closeResults
    } = useResult();

    const { setPublicLegIndex } = useRecalculatePattern();

    /**
     * Handle back navigation within the results view
     */
    const backButtonClick = () => {
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

    return { backButtonClick };
}
