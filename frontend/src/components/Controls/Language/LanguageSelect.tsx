/**
 * @file LanguageSelect.tsx
 * @brief Dropdown component for selecting the currently used language
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

// Language definition including code and flag code
type Language = {
    code: string;
    flagCode: string;
};

// List of all supported languages in the application
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
    showInfo: boolean;      // State whether the information panel is currently visible
    closeInfo: () => void;  // Callback used to close the information panel
}

function LanguageSelect({
    showInfo,
    closeInfo
} : LanguageSelectProps) {
    // i18next instance for language switching
    const { i18n } = useTranslation();

    // Currently active language
    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

    // State storing the selected language
    const [selectedLang, setSelectedLang] = useState<Language>(currentLanguage);

    // State controlling visibility of the dropdown menu
    const [open, setOpen] = useState<boolean>(false);
    
    /**
     * Handles selection of the language 
     * @param lang Selected language
     */
    const handleSelect = (lang: Language) => {
        i18n.changeLanguage(lang.code);
        setSelectedLang(lang);
        setOpen(false);
    };
    
    // State to trigger rerender on window resize
    const [, setCloseDropdown] = useState<boolean>(true);

    /**
     * When the information panel is visible on small screens, 
     * the language selector is hidden
     */
    useEffect(() => {
        const handleResize = () => setCloseDropdown(!(window.innerWidth < 769 && showInfo));
        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [showInfo]);

    return (
        <div className={"controls-select " + (window.innerWidth < 769 && showInfo ? "hidden" : "")}>
            {/* Button opening the language selection dropdown */}
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
                <ExpandMoreIcon 
                    fontSize="small" 
                    className={open ? "rotate" : ""}
                    sx={{ color: 'var(--color-text-primary)' }}
                />
            </button>

            {/* Dropdown menu with available languages */}
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
