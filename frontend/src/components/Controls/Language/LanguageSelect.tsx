/**
 * @file LanguageSelect.tsx
 * @brief Dropdown component for selecting the applications active language
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CustomTooltip from "../../CustomTooltip/CustomTooltip";
import { PUBLIC_URL } from "../../config/config";

// Language representation
type Language = {
    code: string;       // Language code
    flag: string;       // Flag source
};

// List of all supported  application languages
const languages: Language[] = [{
        code: "en",
        flag: `${PUBLIC_URL}img/gb.svg`
    }, {
        code: "cs",
        flag: `${PUBLIC_URL}img/czechia.svg`
    }, {
        code: "sk",
        flag: `${PUBLIC_URL}img/slovakia.svg`
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
                    <img src={selectedLang.flag} alt={selectedLang.code} className="flag" />
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
                            <img src={lang.flag} alt={lang.code} className="flag" />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LanguageSelect;

/** End of file LanguageSelect.tsx */
