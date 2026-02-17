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
import Options from "./Options/Options";
import FindButton from "./FindButton/FindButton";
import { useResult } from "../../ResultContext";
import { useRoute } from "../../Routing/Route";
import Preferences from "./Preferences/Preferences";
import "./Planning.css"

type PlanningProps = {
    closeSidebar: () => void;
};

function Planning({ 
    closeSidebar
}: PlanningProps) {
    const { setResultActiveIndex } = useResult();

    const route = useRoute();

    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        if (!event.currentTarget.checkValidity()) {
            return;
        }
        event.preventDefault();
        setResultActiveIndex(0);
        route(0);
    }
    
    return (
        <form className="planning" onSubmit={handleSubmit} noValidate>
            <div className="sidebar-header">
                <Logo />
            </div>
            <div className="sidebar-content">
                <InputPoints 
                    closeSidebar={closeSidebar}
                />
                <TimeDate />
                <ArrivalDeparture />
                <Options />
                <div className="preferences-find">
                    <Preferences />
                    <FindButton />
                </div>
            </div>
        </form>
    );
}

export default Planning;

/** End of file Planning.tsx */
