/**
 * @file FindButton.tsx
 * @brief Displays a button to plan route in the planning form
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { useResult } from "../../../ResultContext";
import "./FindButton.css";

function FindButton() {
    // Translation function
    const { t } = useTranslation();

    // Result context
    const { loading } = useResult();

    return (
        <button 
            className="find-button"
            disabled={loading}
        >
            {t("planning.find")}
        </button>
    );
}

export default FindButton;

/** End of file FindButton.tsx */
