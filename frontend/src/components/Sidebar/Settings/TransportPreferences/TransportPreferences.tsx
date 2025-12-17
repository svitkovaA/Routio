/**
 * @file TransportPreferences.tsx
 * @brief Display transport preferences in the settings sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import { useSettings } from '../../../SettingsContext';
import Section from '../ModePreferences/Section/Section';
import { useState } from 'react';

function TransportPreferences() {
    const { t } = useTranslation();

    const [isOpen, setIsOpen] = useState<boolean>(false);

    const { 
        maxTransfers,
        setMaxTransfers,
        selectedModes,
        setSelectedModes
    } = useSettings();

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
            <div className="toggle-settings" onClick={() => setIsOpen(!isOpen)}>
                <span>{t("settingsTab.transportPreferences")}</span>
                <FontAwesomeIcon icon={faAngleLeft} className={isOpen ? "rotate90" : ""}/>
            </div>
            <div className={isOpen ? "settings-content" : "settings-content hidden"}>

                <Section
                    label={t("settingsTab.transportPreferencesTab.maxTransfers")}
                    value={maxTransfers}
                    setValue={setMaxTransfers}
                    bounds={{ min:0, max: 10 }}
                />
                
                <div className="section">
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

                <div className="section">
                    <span className="section-label">{t("settingsTab.transportPreferencesTab.travelWithBike")}</span>
                        <Checkbox 
                            defaultChecked 
                        />
                </div>
            </div>
        </div>
    );
}

export default TransportPreferences;

/** End of file TransportPreferences.tsx */
