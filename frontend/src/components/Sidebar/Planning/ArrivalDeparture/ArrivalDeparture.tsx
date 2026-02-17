/**
 * @file ArrivalDeparture.tsx
 * @brief Radio button switch for selecting departure or arrival mode in the planning form
 * @author Andrea Svitková (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import { useInput } from '../../../InputContext';
import "./ArrivalDeparture.css";

function ArrivalDeparture() {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const { arriveBy, setArriveBy } = useInput();

    return (
        <FormControl>
            <RadioGroup 
                row 
                value={arriveBy.toString()}
                onChange={(e) => setArriveBy(e.target.value === "true")}
                className="mode-switch"
            >
                <FormControlLabel 
                    value="false" 
                    control={<Radio />} 
                    label={t("planning.departureArrival.departure")} 
                />
                <FormControlLabel 
                    value="true" 
                    control={<Radio />} 
                    label={t("planning.departureArrival.arrival")} 
                />
            </RadioGroup>
        </FormControl>
    );
}

export default ArrivalDeparture;

/** End of file ArrivalDeparture.tsx */
