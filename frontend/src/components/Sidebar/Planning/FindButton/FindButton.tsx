/**
 * @file FindButton.tsx
 * @brief Displays a button to plan route in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import "./FindButton.css";

type FindButtonProps = {
    disabled: boolean;
}

function FindButton({
    disabled
} : FindButtonProps) {
    const { t } = useTranslation();

    return (
        <button 
            className="find-button"
            disabled={disabled}
        >
            {t("planning.find")}
        </button>
    );
}

export default FindButton;

/** End of file FindButton.tsx */
