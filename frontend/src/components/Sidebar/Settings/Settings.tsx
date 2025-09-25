/**
 * @file Settings.tsx
 * @brief Display settings sidebar component
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import TransportPreferences from "./TransportPreferences/TransportPreferences";
import CyclingPreferences from "./CyclingPreferences/CyclingPreferences";
import BikesharingPreferences from "./BikesharingPreferences.tsx/BikesharingPreferences";
import WalkingPreferences from "./WalkingPreferences/WalkingPreferences";
import "./Settings.css";

type SettingsProps = {
    closeSettings: () => void;
    maxTransfers: number;
    setMaxTransfers: (value: number | ((prev: number) => number)) => void;
    selectedModes: string[];
    setSelectedModes: (modes:string[]) => void;
    maxBikeDistance: number;
    setMaxBikeDistance: (value: number | ((prev: number) => number)) => void;
    bikeAverageSpeed: number;
    setBikeAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxBikesharingDistance: number;
    setMaxBikesharingDistance: (value: number | ((prev: number) => number)) => void;
    bikesharingAverageSpeed: number;
    setBikesharingAverageSpeed: (value: number | ((prev: number) => number)) => void;
    maxWalkDistance: number;
    setMaxWalkDistance: (value: number | ((prev: number) => number)) => void;
    walkAverageSpeed: number;
    setWalkAverageSpeed: (value: number | ((prev: number) => number)) => void;
    bikesharingLockTime: number;
    setBikesharingLockTime: (value: number | ((prev: number) => number)) => void;
    bikeLockTime: number;
    setBikeLockTime: (value: number | ((prev: number) => number)) => void;
    style?: React.CSSProperties;
};

function Settings({ 
    closeSettings, 
    maxTransfers,
    setMaxTransfers,
    selectedModes,
    setSelectedModes,
    maxBikeDistance,
    setMaxBikeDistance,
    bikeAverageSpeed,
    setBikeAverageSpeed,
    maxBikesharingDistance,
    setMaxBikesharingDistance,
    bikesharingAverageSpeed,
    setBikesharingAverageSpeed,
    maxWalkDistance,
    setMaxWalkDistance,
    walkAverageSpeed,
    setWalkAverageSpeed,
    bikesharingLockTime,
    setBikesharingLockTime,
    bikeLockTime,
    setBikeLockTime,
    style 
}: SettingsProps) {
    const [isGeneralOpen, setIsGeneralOpen] = useState(false);
    const [isTransferOpen, setIsTransferOpen] = useState(false);
    const [isCycleOpen, setIsCycleOpen] = useState(false);
    const [isBikesharingOpen, setIsBikesharingOpen] = useState(false);
    const [isWalkingOpen, setIsWalkingOpen] = useState(false);
    const [isWeatherOpen, setIsWeatherOpen] = useState(false);

    const { t } = useTranslation();
    const handleCloseSettings = () => {
        setIsGeneralOpen(false);
        setIsTransferOpen(false);
        setIsCycleOpen(false);
        setIsBikesharingOpen(false);
        setIsWalkingOpen(false);
        setIsWeatherOpen(false);
        closeSettings();
    };

    return (
    <div style={style} className="settings">
        <div className="sidebar-header">
            <button className="back-button" onClick={handleCloseSettings}  >
                <FontAwesomeIcon icon={faAngleLeft} />
            </button>
            <span onClick={handleCloseSettings}>{t("settings")}</span>
        </div>

        <div className="sidebar-content">
            <TransportPreferences 
                isTransportOpen={isTransferOpen}
                setIsTransportOpen={setIsTransferOpen}
                maxTransfers={maxTransfers}
                setMaxTransfers={setMaxTransfers}
                selectedModes={selectedModes}
                setSelectedModes={setSelectedModes}
                className={isTransferOpen ? "opened" : ""}
            />

            <CyclingPreferences 
                isCyclingOpen={isCycleOpen}
                setIsCyclingOpen={setIsCycleOpen}
                maxBikeDistance={maxBikeDistance}
                setMaxBikeDistance={setMaxBikeDistance}
                bikeAverageSpeed={bikeAverageSpeed}
                setBikeAverageSpeed={setBikeAverageSpeed}
                bikeLockTime={bikeLockTime}
                setBikeLockTime={setBikeLockTime}
                className={isCycleOpen ? "opened" : ""}
            />

            <BikesharingPreferences
                isBikesharingOpen={isBikesharingOpen}
                setIsBikesharingOpen={setIsBikesharingOpen}
                maxBikesharingDistance={maxBikesharingDistance}
                setMaxBikesharingDistance={setMaxBikesharingDistance}
                bikesharingAverageSpeed={bikesharingAverageSpeed}
                setBikesharingAverageSpeed={setBikesharingAverageSpeed}
                bikesharingLockTime={bikesharingLockTime}
                setBikesharingLockTime={setBikesharingLockTime}
                className={isBikesharingOpen ? "opened" : ""}
            />

            <WalkingPreferences 
                isWalkingOpen={isWalkingOpen}
                setIsWalkingOpen={setIsWalkingOpen}
                maxWalkDistance={maxWalkDistance}
                setMaxWalkDistance={setMaxWalkDistance}
                walkAverageSpeed={walkAverageSpeed}
                setWalkAverageSpeed={setWalkAverageSpeed}
                className={isWalkingOpen ? "opened" : ""}
            />
        </div>
    </div>
    );
}

export default Settings;

/** End of file Settings.tsx */
