/**
 * @file LanguageSelect.tsx
 * @brief Dropdown component for selecting the applications active language
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CustomTooltip from "../../CustomTooltip/CustomTooltip";

// Language representation
type Language = {
    code: string;       // Language code
    flagCode: string;   // Unicode flag representation
};

// List of all supported  application languages
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

function LanguageSelect() {
    // Translation function and i18n instance
    const { t, i18n } = useTranslation();

    // Currently active language
    const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

    // Stores the selected language
    const [selectedLang, setSelectedLang] = useState<Language>(currentLanguage);

    // Controls visibility of the dropdown menu
    const [open, setOpen] = useState<boolean>(false);
    
    /**
     * Handles language selection
     * @param lang Selected language
     */
    const handleSelect = (lang: Language) => {
        i18n.changeLanguage(lang.code);
        setSelectedLang(lang);
        setOpen(false);
    };

    return (
        <div className={"controls-select " + (window.innerWidth < 768)}>
            
            {/* Button opening the language selection dropdown */}
            <CustomTooltip title={t("tooltips.controls.language")} disableTooltip={open}>
                <button
                    onBlur={() => setOpen(false)}
                    className={"controls-button " + (open ? "open" : "")}
                    onClick={() => {
                        setOpen(!open);
                    }}
                >
                    {selectedLang.flagCode}
                    <ExpandMoreIcon 
                        fontSize="small" 
                        className={open ? "rotate" : ""}
                        sx={{ color: 'var(--color-text-primary)' }}
                    />
                </button>
            </CustomTooltip>

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
