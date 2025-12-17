/**
 * @file Planning.tsx
 * @brief Displays the main trip planning component, including waypoints input, time and date selection, routing options, settings and info controls, and the find button
 * @author Andrea Svitkova (xsvitka00)
 */

import "dayjs/locale/cs"; 
import Logo from "./Logo/Logo";
import InputPoints from "./InputPoints/InputPoints";
import TimeDate from "./TimeDate/TimeDate";
import ArrivalDeparture from "./ArrivalDeparture/ArrivalDeparture";
import InfoSettings from "./InfoSettings/InfoSettings";
import Options from "./Options/Options";
import FindButton from "./FindButton/FindButton";
import { useResult } from "../../ResultContext";

type PlanningProps = {
    showSettings: () => void;
    showInfo: () => void;
    closeSidebar: () => void;
    selectMultimodalResult: () => void;
};

function Planning({ 
        showSettings, 
        showInfo, 
        closeSidebar, 
        selectMultimodalResult,
}: PlanningProps) {
    const { setLoading } = useResult();

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        if (!event.currentTarget.checkValidity()) {
            return;
        }
        event.preventDefault();
        selectMultimodalResult();
        setLoading(true);
    }
    
    return (
        <form className="planning" onSubmit={handleSubmit}>
            <div className="sidebar-header">
                <Logo />
            </div>
            <div className="sidebar-content">
                <InputPoints 
                    closeSidebar={closeSidebar}
                />
                <TimeDate />
                <ArrivalDeparture />
                <InfoSettings 
                    showSettings={showSettings}
                    showInfo={showInfo}
                />
                <Options />
                <FindButton />
            </div>
        </form>
    );
}

export default Planning;

/** End of file Planning.tsx */
