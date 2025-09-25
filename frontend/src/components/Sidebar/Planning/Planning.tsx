/**
 * @file Planning.tsx
 * @brief Displays the main trip planning component, including waypoints input, time and date selection, routing options, settings and info controls, and the find button
 * @author Andrea Svitkova (xsvitka00)
 */

import { Waypoint, LegPreference, RoutePreference } from '../../types/types';
import dayjs from "dayjs";
import "dayjs/locale/cs"; 
import Logo from "./Logo/Logo";
import InputPoints from "./InputPoints/InputPoints";
import TimeDate from "./TimeDate/TimeDate";
import ArrivalDeparture from "./ArrivalDeparture/ArrivalDeparture";
import InfoSettings from "./InfoSettings/InfoSettings";
import Options from "./Options/Options";
import FindButton from "./FindButton/FindButton";

type PlanningProps = {
    showSettings: () => void;
    showInfo: () => void;
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[] | ((prev: Waypoint[]) => Waypoint[])) => void;
    setMapSelectionIndex: (value: number) => void;
    closeSidebar: () => void;
    selectMultimodalResult: () => void;
    legPreferences: LegPreference[];
    setLegPreferences: (value: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    time: dayjs.Dayjs;
    date: dayjs.Dayjs;
    setTime: (value: dayjs.Dayjs) => void;
    setDate: (value: dayjs.Dayjs) => void;
    arriveBy: boolean;
    setArriveBy: (value: boolean) => void;
    useOwnBike: boolean;
    setUseOwnBike: (value: boolean) => void;
    activeField: number | null;
    setActiveField: (value: number | null) => void;
    clearWaypoint: (index: number, clearDisplayName: boolean) => void;
    removeWaypoint: (currentIndex: number) => void;
    preference: RoutePreference;
    setPreference: (value: RoutePreference) => void;
    findButtonDisabled: boolean;
    disableFindButton: () => void;
    style?: React.CSSProperties;
};

function Planning({ 
        showSettings, 
        showInfo, 
        waypoints, 
        setWaypoints, 
        setMapSelectionIndex, 
        closeSidebar, 
        selectMultimodalResult,
        legPreferences,
        setLegPreferences,
        time,
        date,
        setTime,
        setDate,
        arriveBy,
        setArriveBy,
        useOwnBike,
        setUseOwnBike,
        activeField,
        setActiveField,
        clearWaypoint,
        removeWaypoint,
        preference,
        setPreference,
        findButtonDisabled,
        disableFindButton,
        style 
    }: PlanningProps) {

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        if (!event.currentTarget.checkValidity()) {
            return;
        }
        event.preventDefault();
        selectMultimodalResult();
        disableFindButton();
    }
    
    return (
        <form className="planning" style={style} onSubmit={handleSubmit}>
            <div className="sidebar-header">
                <Logo />
            </div>
            <div className="sidebar-content">
                <InputPoints 
                    waypoints={waypoints}
                    setWaypoints={setWaypoints}
                    setMapSelectionIndex={setMapSelectionIndex}
                    closeSidebar={closeSidebar}
                    legPreferences={legPreferences}
                    setLegPreferences={setLegPreferences}
                    activeField={activeField}
                    setActiveField={setActiveField}
                    clearWaypoint={clearWaypoint}
                    removeWaypoint={removeWaypoint}
                />
                <TimeDate 
                    time={time}
                    date={date}
                    setTime={setTime}
                    setDate={setDate}
                />
                <ArrivalDeparture 
                    arriveBy={arriveBy}
                    setArriveBy={setArriveBy}
                />
                <InfoSettings 
                    showSettings={showSettings}
                    showInfo={showInfo}
                />
                <Options 
                    useOwnBike={useOwnBike}
                    setUseOwnBike={setUseOwnBike}
                    preference={preference}
                    setPreference={setPreference}
                />
                <FindButton 
                    disabled={findButtonDisabled}
                />
            </div>
        </form>
    );
}

export default Planning;

/** End of file Planning.tsx */
