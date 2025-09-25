/**
 * @file TimeDate.tsx
 * @brief Displays date and time inputs in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import dayjs from "dayjs";
import "dayjs/locale/cs"; 
import { useTranslation } from "react-i18next";
import "./TimeDate.css";


type TimeDateProps = {
    time: dayjs.Dayjs;
    date: dayjs.Dayjs;
    setTime: (value: dayjs.Dayjs) => void;
    setDate: (value: dayjs.Dayjs) => void;
}

function TimeDate({
    time,
    date,
    setTime,
    setDate
} : TimeDateProps){
    const { t } = useTranslation();
    
    return (
        <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"cs"}>
            <div className="grid-wrapper time-date">
                <DatePicker
                    label={t("planning.date")}
                    value={date}
                    onChange={(newValue) => {if (newValue !== null) setDate(newValue)}}
                    slotProps={{
                        textField: {
                            InputLabelProps: { shrink: true }
                        }
                    }}
                />
                <TimePicker
                    label={t("planning.time")}
                    value={time}
                    ampm={false}
                    onChange={(newValue) => {if (newValue !== null) setTime(newValue)}}
                    slotProps={{
                        actionBar: { actions: ['accept'] }
                    }}
                />
            </div>
        </LocalizationProvider>
    );
}

export default TimeDate;

/** End of file TimeDate.tsx */
