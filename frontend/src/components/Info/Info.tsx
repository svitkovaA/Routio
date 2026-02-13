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
import About from "./About/About";
import HowToUse from "./HowToUse/HowToUse";
import Features from "./Features/Features";
import Contact from "./Contact/Contact";
import { createPortal } from "react-dom";
import Logo from "../Sidebar/Planning/Logo/Logo";
import "./Info.css";

type InfoProps = {
    closeInfo: () => void,
};

function Info({ closeInfo }: InfoProps) {
    type InfoTab = "about" | "howto" | "features" | "contact";
    const [tab, setTab] = useState<InfoTab>("about");
    const { t } = useTranslation();

    const isDesktop = useMediaQuery('(min-width:768px)');
    const [menuOpen, setMenuOpen] = useState<boolean>(false);

    const keepOpen = (e: React.MouseEvent) => {
        e.stopPropagation();
    }

    return createPortal(
        <div className="info-wrapper" onClick={closeInfo}>
            <div className="info" onClick={keepOpen}>
    
                <div className="info-header">
                    {!isDesktop && (
                        <button
                        className="mobile-menu-button"
                        onClick={() => setMenuOpen(prev => !prev)}
                        >
                            <MenuIcon />
                        </button>
                    )}
                    <Logo />
                    <button className="close-button" onClick={closeInfo}>
                        <CloseIcon />
                    </button>
                </div>


                {isDesktop ? (
                    <div className="info-grid-wrapper">
                        <h3
                            className={`input-wrapper ${tab === "about" ? "selected" : ""}`}
                            onClick={() => setTab("about")}
                        >
                            {t("informationTab.overview")}
                        </h3>

                        <h3
                            className={`input-wrapper ${tab === "howto" ? "selected" : ""}`}
                            onClick={() => setTab("howto")}
                        >
                            {t("informationTab.howToUse")}
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
                        {menuOpen && (
                            <div className="mobile-menu">
                                <div onClick={() => { setTab("about"); setMenuOpen(false); }}>
                                    {t("informationTab.overview")}
                                </div>
                                <div onClick={() => { setTab("howto"); setMenuOpen(false); }}>
                                    {t("informationTab.howToUse")}
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
        </div>,
        document.body
    );
}

export default Info;

/** End of file Info.tsx */
