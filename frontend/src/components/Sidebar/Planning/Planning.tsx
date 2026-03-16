/**
 * @file Planning.tsx
 * @brief Route planning component
 * @author Andrea Svitkova (xsvitka00)
 */

import "dayjs/locale/cs"; 
import Logo from "./Logo/Logo";
import InputPoints from "./InputPoints/InputPoints";
import TimeDate from "./TimeDate/TimeDate";
import ArrivalDeparture from "./ArrivalDeparture/ArrivalDeparture";
import Options from "./Options/Options";
import FindButton from "./FindButton/FindButton";
import { useResult } from "../../Contexts/ResultContext";
import { useRoute } from "../../Routing/Route";
import Preferences from "./Preferences/Preferences";
import { useInput } from "../../Contexts/InputContext";
import "./Planning.css"

type PlanningProps = {
    closeSidebar: () => void;   // Callback for closing the sidebar
};

function Planning({ 
    closeSidebar
}: PlanningProps) {
    // Result context
    const { setResultActiveIndex } = useResult();

    // Routing controller hook
    const route = useRoute();

    // User input context
    const { waypoints, setFieldErrors } = useInput();

    // Form submit handler
    const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
        // Prevent default form submission behavior
        event.preventDefault();

        const invalidIndexes: number[] = [];

        // Validate waypoints
        waypoints.forEach((wp, index) => {
            if (wp.displayName.trim() === "" && wp.lat === 0 && wp.lon === 0) {
                invalidIndexes.push(index);
            }
        });

        // If there are invalid fields, store their indices and stop submission
        if (invalidIndexes.length > 0) {
            setFieldErrors(invalidIndexes);
            return;
        }

        // Clear previous validation errors
        setFieldErrors([]);

        // Activate first result container
        setResultActiveIndex(0);

        // Trigger multimodal routing computation
        route(0);
    }
    
    return (
        <form className="planning" onSubmit={handleSubmit} noValidate>
            {/* Application header with logo */}
            <div className="sidebar-header">
                <Logo />
            </div>

            {/* Input form content */}
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
