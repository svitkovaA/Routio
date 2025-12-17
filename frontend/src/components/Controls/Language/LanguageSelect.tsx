/**
 * @file LanguageSelect.tsx
 * @brief Language selection dropdown component with flag icons, language switch integrated using i18next
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleDown } from "@fortawesome/free-solid-svg-icons";
import { useTranslation } from "react-i18next";

type Language = {
    code: string;
    flagCode: string;
};

const languages: Language[] = [{
        code: "en",
        flagCode: "\uD83C\uDDEC\uD83C\uDDE7"
    }, {
        code: "cs",
        flagCode: "\uD83C\uDDE8\uD83C\uDDFF"
    }, {
        code: "sk",
        flagCode: "\uD83C\uDDF8\uD83C\uDDF0"
    }
];

type LanguageSelectProps = {
    showInfo: boolean;
    closeInfo: () => void;
}

function LanguageSelect({
    showInfo,
    closeInfo
} : LanguageSelectProps) {
    const { i18n } = useTranslation();
    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];
    const [selectedLang, setSelectedLang] = useState<Language>(currentLanguage);
    const [open, setOpen] = useState<boolean>(false);
    
    const handleSelect = (lang: Language) => {
        i18n.changeLanguage(lang.code);
        setSelectedLang(lang);
        setOpen(false);
    };
    
    const [_, setCloseDropdown] = useState<boolean>(true);
    useEffect(() => {
        const handleResize = () => setCloseDropdown(!(window.innerWidth < 769 && showInfo));
        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [showInfo]);

    return (
        <div className={"controls-select " + (window.innerWidth < 769 && showInfo ? "hidden" : "")}>
            <button
                onBlur={() => setOpen(false)}
                className={"controls-button " + (open ? "open" : "")}
                onClick={() => {
                    if (showInfo) {
                        closeInfo();
                    }
                    else {
                        setOpen(!open);
                    }
                }}
            >
                {selectedLang.flagCode}
                <FontAwesomeIcon icon={faAngleDown} className={open ? "rotate" : ""} />
            </button>

            {open && (
                <div className="dropdown">
                    {languages.map((lang) => (
                        <div
                            key={lang.code}
                            className={"dropdown-item " + (lang.code === selectedLang.code ? "selected" : "")}
                            onMouseDown={() => handleSelect(lang)}
                        >
                            {lang.flagCode}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LanguageSelect;

/** End of file LanguageSelect.tsx */
