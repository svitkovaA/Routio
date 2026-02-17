/**
 * @file Info.tsx
 * @brief Displays information about the application
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { createPortal } from "react-dom";
import CloseIcon from '@mui/icons-material/Close';
import useMediaQuery from '@mui/material/useMediaQuery';
import MenuIcon from '@mui/icons-material/Menu';
import { useTranslation } from "react-i18next";
import Logo from "../Sidebar/Planning/Logo/Logo";
import About from "./About/About";
import HowToUse from "./HowToUse/HowToUse";
import Features from "./Features/Features";
import Contact from "./Contact/Contact";
import "./Info.css";

type InfoProps = {
    closeInfo: () => void,  // Callback for closing the information panel
};

function Info({ closeInfo }: InfoProps) {
    // Translation function
    const { t } = useTranslation();

    // Information tabs
    type InfoTab = "about" | "howto" | "features" | "contact";

    // Currently active tab
    const [tab, setTab] = useState<InfoTab>("about");

    // Determines whether desktop layout should be used
    const isDesktop = useMediaQuery('(min-width:768px)');

    // Controls visibility of the navigation menu on mobile devices
    const [menuOpen, setMenuOpen] = useState<boolean>(false);

    // Prevents the planel from closing when clicking inside its content
    const keepOpen = (e: React.MouseEvent) => {
        e.stopPropagation();
    }

    return createPortal(
        <div className="info-wrapper" onClick={closeInfo}>
            <div className="info" onClick={keepOpen}>
    
                {/* Information panel header with optional mobile toggle, logo and close button */}
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

                {/* Navigation tabs */}
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

                {/* Information panel content */}
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
