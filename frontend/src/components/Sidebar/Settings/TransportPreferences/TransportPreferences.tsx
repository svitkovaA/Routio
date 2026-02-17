/**
 * @file TransportPreferences.tsx
 * @brief Components for configuring public transport preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import Checkbox from '@mui/material/Checkbox';
import { useTranslation } from "react-i18next";
import { useSettings } from '../../../SettingsContext';
import Section from '../ModePreferences/Section/Section';
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import "./TransportPreferences.css";

function TransportPreferences() {
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
     * @param mode Transport mode identifier
     */
    const handleModeSelection = (mode: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.checked) {
            if (!selectedModes.includes(mode)) {
                setSelectedModes([...selectedModes, mode]);
            }
        }
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
                        <KeyboardArrowLeftIcon 
                            fontSize="large" 
                            className={isOpen ? "rotate90" : ""} 
                            sx={{ color: 'var(--color-text-primary)' }}
                        />
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
                                        <CustomTooltip title={selectedModes.includes(mode.value) ? "asdf" : "nn"}>
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
