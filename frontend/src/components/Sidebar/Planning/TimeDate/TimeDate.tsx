/**
 * @file TimeDate.tsx
 * @brief Displays date and time inputs in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import "dayjs/locale/cs"; 
import { useTranslation } from "react-i18next";
import "./TimeDate.css";
import { useInput } from '../../../InputContext';

function TimeDate(){
    const { t } = useTranslation();

    const {
        date, setDate,
        time, setTime
    } = useInput();
    
    return (
        <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"cs"}>
            <div className="grid-wrapper time-date">
                <DatePicker
                    label={t("planning.date")}
                    value={date}
                    onChange={(newValue) => {if (newValue !== null) setDate(newValue)}}
                    sx={{ 
                        '& .MuiSvgIcon-root': {
                            color: 'var(--color-icons)',
                        }
                    }}
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
                    sx={{ 
                        '& .MuiSvgIcon-root': {
                            color: 'var(--color-icons)',
                        }
                    }}
                />
            </div>
        </LocalizationProvider>
    );
}

export default TimeDate;

/** End of file TimeDate.tsx */
