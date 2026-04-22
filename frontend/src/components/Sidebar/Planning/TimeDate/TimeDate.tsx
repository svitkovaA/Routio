/**
 * @file TimeDate.tsx
 * @brief Displays date and time inputs in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from 'react';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { csCZ, enUS, skSK } from '@mui/x-date-pickers/locales';
import RestoreIcon from '@mui/icons-material/Restore';
import IconButton from "@mui/material/IconButton";
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import dayjs from "dayjs";
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
    const pickerLocaleMap: Record<string, typeof csCZ> = {
        cs: csCZ,
        sk: skSK,
        en: enUS,
    };

    // Selects appropriate picker localization based on the language
    const currentPickerLocale = pickerLocaleMap[i18n.language.split("-")[0]] || enUS;

    // English is selected
    const isEnglish = i18n.language.split("-")[0] === "en";

    // Determines whether the selected date and time correspond to real time
    const isNow = (() => {
        if (!date || !time) return false;

        const now = dayjs();
        return (
            // Check the selected date
            date.isSame(now, "day") &&
            // Check the selected time
            time.isSame(now, "minute")
        );
    })();

    // State used only to force component re-render based on time
    const [, setTick] = useState<number>(0);

    /**
     * Synchronizes the component with real time
     */
    useEffect(() => {
        // Function that triggers re-render
        const update = () => setTick(prev => prev + 1);

        const now = dayjs();

        // Calculate milliseconds remaining until the next full minute
        const msToNextMinute =
            60000 - (now.second() * 1000 + now.millisecond());

        let interval: NodeJS.Timeout;

        // Wait until the start of the next minute
        const timeout = setTimeout(() => {
            update();
            // Start interval updates
            interval = setInterval(update, 60000);
        }, msToNextMinute);

        return () => {
            clearTimeout(timeout);
            if (interval) clearInterval(interval);
        };
    }, []);

    return (
        <LocalizationProvider 
            dateAdapter={AdapterDayjs} 
            adapterLocale={i18n.language.split("-")[0] || "cs"}
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
                    className="time-input"
                    label={t("planning.time")}
                    value={time}
                    ampm={isEnglish}
                    onChange={(newValue) => {
                        if (newValue !== null) setTime(newValue.second(0).millisecond(0))
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
                {!isNow && (
                    <CustomTooltip title={t("tooltips.inputForm.leaveNow")}>
                        <IconButton
                            className="now-button"
                            onClick={() => {
                                setTime(dayjs().second(0).millisecond(0));
                                setDate(dayjs().second(0).millisecond(0));
                            }}
                            size="small"
                        >
                            <RestoreIcon sx={{ fontSize: 15 }}/>
                            <span>{t("planning.now")}</span>
                        </IconButton>
                    </CustomTooltip>
                )}
            </div>
        </LocalizationProvider>
    );
}

export default TimeDate;

/** End of file TimeDate.tsx */
