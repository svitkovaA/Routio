/**
 * @file ArrivalDeparture.tsx
 * @brief Radio button switch for selecting departure or arrival mode in the planning sidebar
 * @author Andrea Svitková (xsvitka00)
 */

import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import { useTranslation } from "react-i18next";
import "./ArrivalDeparture.css";
import { useInput } from '../../../InputContext';

function ArrivalDeparture() {
    const { t } = useTranslation();

    const {
        arriveBy, setArriveBy
    } = useInput();
    return (
        <FormControl>
            <RadioGroup 
                row 
                value={arriveBy.toString()}
                onChange={(e) => setArriveBy(e.target.value === "true")}
                className="mode-switch"
            >
                <FormControlLabel value="false" control={<Radio />} label={t("planning.departureArrival.departure")} />
                <FormControlLabel value="true" control={<Radio />} label={t("planning.departureArrival.arrival")} />
            </RadioGroup>
        </FormControl>
    );
}

export default ArrivalDeparture;

/** End of file ArrivalDeparture.tsx */
