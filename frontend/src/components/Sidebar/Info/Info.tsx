/**
 * @file Info.tsx
 * @brief Displays information about the app and the usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faXmark } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import "./Info.css";

type InfoProps = {
    closeInfo: () => void,
};

function Info({ closeInfo }: InfoProps) {
    const [showAbout, setShowAbout] = useState(true);
    const { t } = useTranslation();

    const keepOpen = (e: React.MouseEvent) => {
        e.stopPropagation();
    }

    return (
        <div className="info-wrapper" onClick={closeInfo}>
            <div className="info" onClick={keepOpen}>
                <button className="close-button" onClick={closeInfo}>
                    <FontAwesomeIcon icon={faXmark} />
                </button>
                <h2>{t("information")}</h2>
                <div className="grid-wrapper">
                    <h3 
                        className={showAbout ? "input-wrapper selected" : "input-wrapper"} 
                        onClick={() => setShowAbout(true)}
                    >
                        {t("informationTab.about")}
                    </h3>
                    <h3 
                        className={showAbout ? "input-wrapper" : "input-wrapper selected"} 
                        onClick={() => setShowAbout(false)}
                    >
                        {t("informationTab.gettingStarted")}
                    </h3>
                </div>
                <div className="text-wrapper">
                    <div className={showAbout ? "" : "hidden"}>
                        About the app content
                    </div>
                    <div className={showAbout ? "hidden" : ""}>
                        Getting started content
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Info;

/** End of file Info.tsx */
