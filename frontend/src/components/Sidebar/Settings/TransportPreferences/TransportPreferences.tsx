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
import { IconButton, TextField, InputAdornment } from "@mui/material";
import { faPlus, faMinus } from '@fortawesome/free-solid-svg-icons';
import './TransportPreferences.css'


type TransportSettingsProps = {
    isTransportOpen: boolean;
    setIsTransportOpen: (isOpen: boolean) => void;
    maxTransfers: number;
    setMaxTransfers: (value: number | ((prev: number) => number)) => void;
    selectedModes: string[];
    setSelectedModes: (modes:string[]) => void;
    className?: string;
};

function TransportPreferences({ 
    isTransportOpen, 
    setIsTransportOpen, 
    maxTransfers,
    setMaxTransfers,
    selectedModes,
    setSelectedModes,
    className 
} : TransportSettingsProps) {
    const { t } = useTranslation();

    const handleChangeMaxTransfers = (e: React.ChangeEvent<HTMLInputElement>) => {
        let value = Number(e.target.value);
        if (value < 0) {
            value = 0;
        }
        if (value > 10) {
            value = 10;
        }
        setMaxTransfers(value);
    };

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
        <div className={"settings-section " + className}>
            <div className="toggle-settings" onClick={() => setIsTransportOpen(!isTransportOpen)}>
                <span>{t("settingsTab.transportPreferences")}</span>
                <FontAwesomeIcon icon={faAngleLeft} className={isTransportOpen ? "rotate90" : ""}/>
            </div>
            <div className={isTransportOpen ? "settings-content" : "settings-content hidden"}>

                <div className="section">
                    <span className="section-label">
                        {t("settingsTab.transportPreferencesTab.maxTransfers")}
                    </span>
                    <TextField
                        type="number"
                        value={maxTransfers}
                        onChange={handleChangeMaxTransfers}
                        className="number-input"
                        InputProps={{
                            inputProps: { min: 0, max: 10, step: 1 },
                            endAdornment: (
                            <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>
                                <IconButton onClick={() => setMaxTransfers(prev => Math.max(0, prev - 1))} size="small">
                                    <FontAwesomeIcon className="fa-icon" icon={faMinus} />
                                </IconButton>
                                <IconButton onClick={() => setMaxTransfers(prev => Math.min(10, prev + 1))} size="small">
                                    <FontAwesomeIcon className="fa-icon" icon={faPlus} />
                                </IconButton>
                            </InputAdornment>
                            )
                        }}
                    />
                </div>
                
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
