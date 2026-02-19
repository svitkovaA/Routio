/**
 * @file TransportPreferences.tsx
 * @brief Components for configuring public transport preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import { useTranslation } from "react-i18next";
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import Checkbox from '@mui/material/Checkbox';
import Section from '../ModePreferences/Section/Section';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import { useSettings } from '../../../SettingsContext';
import "./TransportPreferences.css";

function TransportPreferences() {
    // Translation function
    const { t } = useTranslation();

    // State controlling section expansion
    const [isOpen, setIsOpen] = useState<boolean>(false);

    // Settings context
    const { 
        maxTransfers,
        setMaxTransfers,
        selectedModes,
        setSelectedModes
    } = useSettings();

    // List of supported public transport modes
    const transportModes = [
        { value: "bus", labelKey: "bus" },
        { value: "tram", labelKey: "tram" },
        { value: "rail", labelKey: "train" },
        { value: "trolleybus", labelKey: "trolleybus" },
        { value: "metro", labelKey: "subway" },
        { value: "water", labelKey: "boat" },
    ];

    /**
     * Handles selection and deselection of transport modes
     * 
     * @param mode Transport mode identifier
     */
    const handleModeSelection = (mode: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
        // If checkbox was checked
        if (event.target.checked) {

            // Prevent duplicate entries in selectedModes
            if (!selectedModes.includes(mode)) {
                // Add selected mode to the list
                setSelectedModes([...selectedModes, mode]);
            }
        }
        // Remove mode from selectedModes when unchecked
        else {
            setSelectedModes(selectedModes.filter(m => m !== mode));
        }
    };

    return (
        <div className={"settings-section " + (isOpen ? "opened" : "")}>
            {/* Section toggle */}
            <div className="toggle-settings" onClick={() => setIsOpen(!isOpen)}>
                <span>{t("settingsTab.transportPreferences")}</span>
                <CustomTooltip title={t("tooltips.settings.openSections.openTransportPreferences")}>
                    <CustomTooltip title={isOpen ? t("tooltips.settings.openSections.closeTransportPreferences") : t("tooltips.settings.openSections.openTransportPreferences")}>
                        <KeyboardArrowLeftIcon
                            fontSize="large" 
                            className={isOpen ? "rotate90" : ""} 
                            sx={{ color: 'var(--color-text-primary)' }}
                        />
                    </CustomTooltip>
                </CustomTooltip>
            </div>
            <div className={isOpen ? "settings-content" : "settings-content hidden"}>
            {/* Maximum transfers preference */}
                <Section
                    label={t("settingsTab.transportPreferencesTab.maxTransfers")}
                    value={maxTransfers}
                    setValue={setMaxTransfers}
                    bounds={{ min:0, max: 10 }}
                />
                
                {/* Transport mode selection */}
                <div className="section transport-modes">
                    <span className="section-label">
                        {t("settingsTab.transportPreferencesTab.transportModes")}
                    </span>

                    {/* Transport modes checkboxes */}
                    <FormGroup className="options">
                        {transportModes.map((mode) => (
                            <FormControlLabel
                                key={mode.value}
                                control={
                                    <CustomTooltip title={selectedModes.includes(mode.value) ? t("tooltips.settings.removeMode") : t("tooltips.settings.addMode")}>
                                        <Checkbox
                                            checked={selectedModes.includes(mode.value)}
                                            onChange={handleModeSelection(mode.value)}
                                        />
                                    </CustomTooltip>
                                }
                                label={t(`settingsTab.transportPreferencesTab.${mode.labelKey}`)}
                            />
                        ))}
                    </FormGroup>
                </div>
            </div>
        </div>
    );
}

export default TransportPreferences;

/** End of file TransportPreferences.tsx */
