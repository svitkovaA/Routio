/**
 * @file Info.tsx
 * @brief Displays information about the app and the usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import CloseIcon from '@mui/icons-material/Close';
import { useTranslation } from "react-i18next";
import useMediaQuery from '@mui/material/useMediaQuery';
import MenuIcon from '@mui/icons-material/Menu';
import "./Info.css";
import About from "./About/About";
import HowToUse from "./HowToUse/HowToUse";
import Features from "./Features/Features";
import Contact from "./Contact/Contact";

type InfoProps = {
    closeInfo: () => void,
};

function Info({ closeInfo }: InfoProps) {
    type InfoTab = "about" | "howto" | "features" | "contact";
    const [tab, setTab] = useState<InfoTab>("about");
    const { t } = useTranslation();

    const isNotebook = useMediaQuery('(min-width:768px)');
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <div className="info">
            <button className="close-button" onClick={closeInfo}>
                <CloseIcon />
            </button>

            <h2>{t("information")}</h2>

            {isNotebook ? (
                <div className="grid-wrapper">
                    <h3
                        className={`input-wrapper ${tab === "about" ? "selected" : ""}`}
                        onClick={() => setTab("about")}
                    >
                        {t("informationTab.about")}
                    </h3>

                    <h3
                        className={`input-wrapper ${tab === "howto" ? "selected" : ""}`}
                        onClick={() => setTab("howto")}
                    >
                        {t("informationTab.howTo")}
                    </h3>

                    <h3
                        className={`input-wrapper ${tab === "features" ? "selected" : ""}`}
                        onClick={() => setTab("features")}
                    >
                        {t("informationTab.features")}
                    </h3>

                    <h3
                        className={`input-wrapper ${tab === "contact" ? "selected" : ""}`}
                        onClick={() => setTab("contact")}
                    >
                        {t("informationTab.contact")}
                    </h3>
                </div>
            ) : (
                <div className="mobile-navigation">
                    <button
                        className="mobile-menu-button"
                        onClick={() => setMenuOpen(prev => !prev)}
                    >
                        <MenuIcon />
                    </button>

                    {menuOpen && (
                        <div className="mobile-menu">
                            <div onClick={() => { setTab("about"); setMenuOpen(false); }}>
                                {t("informationTab.about")}
                            </div>
                            <div onClick={() => { setTab("howto"); setMenuOpen(false); }}>
                                {t("informationTab.howTo")}
                            </div>
                            <div onClick={() => { setTab("features"); setMenuOpen(false); }}>
                                {t("informationTab.features")}
                            </div>
                            <div onClick={() => { setTab("contact"); setMenuOpen(false); }}>
                                {t("informationTab.contact")}
                            </div>
                        </div>
                    )}
                </div>
            )}

            <div className="text-wrapper">
            {tab === "about" && <About />}
            {tab === "howto" && <HowToUse />}
            {tab === "features" && <Features />}
            {tab === "contact" && <Contact />}
            </div>
        </div>
    );
}

export default Info;

/** End of file Info.tsx */
