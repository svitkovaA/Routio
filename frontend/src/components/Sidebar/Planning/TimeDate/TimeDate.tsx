/**
 * @file TimeDate.tsx
 * @brief Displays date and time inputs in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { csCZ, enUS, skSK } from '@mui/x-date-pickers/locales';
import { useInput } from '../../../Contexts/InputContext';
import { useTranslation } from "react-i18next";
import "dayjs/locale/cs"; 
import "dayjs/locale/en"; 
import "dayjs/locale/sk"; 
import "./TimeDate.css";

function TimeDate(){
    // Translation function and i18 instance
    const { t, i18n } = useTranslation();

    // User input context
    const {
        date, setDate,
        time, setTime
    } = useInput();

    // Maps application language codes to MUI picker locales
    const pickerLocaleMap: Record<string, any> = {
        cs: csCZ,
        sk: skSK,
        en: enUS,
    };

    // Selects appropriate picker localization based on the language
    const currentPickerLocale = pickerLocaleMap[i18n.language] || enUS;

    // English is selected
    const isEnglish = i18n.language === "en";

    return (
        <LocalizationProvider 
            dateAdapter={AdapterDayjs} 
            adapterLocale={i18n.language || "cs"}
            localeText={currentPickerLocale.components.MuiLocalizationProvider.defaultProps.localeText}
        >
            <div className="grid-wrapper time-date">
                {/* Date selection */}
                <DatePicker
                    label={t("planning.date")}
                    value={date}
                    onChange={(newValue) => {
                        if (newValue !== null) setDate(newValue)
                    }}
                    sx={{ 
                        '& .MuiSvgIcon-root': {
                            color: 'var(--color-icons)',
                        }
                    }}
                    slotProps={{
                        textField: {
                            InputLabelProps: { shrink: true }
                        },
                        openPickerButton: {
                            tabIndex: -1
                        }
                    }}
                />

                {/* Time selection */}
                <TimePicker
                    label={t("planning.time")}
                    value={time}
                    ampm={isEnglish ? true : false}
                    onChange={(newValue) => {
                        if (newValue !== null) setTime(newValue)
                    }}
                    sx={{ 
                        '& .MuiSvgIcon-root': {
                            color: 'var(--color-icons)',
                        }
                    }}
                    slotProps={{
                        actionBar: { actions: ['accept'] },
                        openPickerButton: {
                            tabIndex: -1
                        }
                    }}
                />
            </div>
        </LocalizationProvider>
    );
}

export default TimeDate;

/** End of file TimeDate.tsx */
