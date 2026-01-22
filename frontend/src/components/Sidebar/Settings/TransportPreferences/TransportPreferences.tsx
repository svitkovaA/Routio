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
                <KeyboardArrowLeftIcon 
                    fontSize="large" 
                    className={isOpen ? "rotate90" : ""} 
                    sx={{ color: 'var(--color-text-primary)' }}
                />
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
                    <span className="section-label">{t("settingsTab.transportPreferencesTab.transportModes")}</span>
                    <FormGroup className="options">
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("bus")}
                                onChange={handleModeSelection("bus")}
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.bus")} />
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("tram")}
                                onChange={handleModeSelection("tram")} 
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.tram")} />
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("rail")}
                                onChange={handleModeSelection("rail")} 
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.train")} />
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("trolleybus")}
                                onChange={handleModeSelection("trolleybus")}
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.trolleybus")} />
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("metro")}
                                onChange={handleModeSelection("metro")}
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.subway")} />
                        <FormControlLabel control={
                            <Checkbox 
                                checked={selectedModes.includes("water")}
                                onChange={handleModeSelection("water")} 
                            />
                        } 
                        label={t("settingsTab.transportPreferencesTab.boat")} />
                    </FormGroup>
                </div>
            </div>
        </div>
    );
}

export default TransportPreferences;

/** End of file TransportPreferences.tsx */
