/**
 * @file WaitSelect.tsx
 * @brief Component for selecting wait time between locations
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { TimePicker } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import dayjs from "dayjs";
import { useInput } from "../../../../../InputContext";
import CustomTooltip from "../../../../../CustomTooltip/CustomTooltip";

type WaitSelectProps = {
    index: number;      // Index of the leg in legPreferences array
}

function WaitSelect({ index }: WaitSelectProps) {
    // Translation function
    const { t } = useTranslation()

    // User input context
    const {
        legPreferences, setLegPreferences
    } = useInput();
    
    /**
     * Updates waiting time for the selected leg
     * 
     * @param value Selected time value
     */
    const handleSelect = (value: dayjs.Dayjs) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            newLegPreferences[index] = { ...newLegPreferences[index], wait: value};
            
            return newLegPreferences;
        });
    }
    
    return (
        <div className="select wait-select">
            <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"cs"}>
                <CustomTooltip title={t("tooltips.inputForm.timeInWaypoint")}>
                    <div>
                        <TimePicker
                            value={legPreferences[index].wait}
                            ampm={false}
                            onChange={(newValue) => {if (newValue !== null) handleSelect(newValue)}}
                            slotProps={{
                                actionBar: { actions: ['accept'] },
                                textField: {                            
                                    sx: {
                                        '& .MuiPickersInputBase-root': {
                                            height: '30px',
                                            bottom: '1px',
                                            backgroundColor: 'var(--color-item-hover)',
                                            borderRadius: '6px'
                                        },
                                        '& .MuiPickersOutlinedInput-notchedOutline': {
                                            border: '1px solid black',
                                            borderRadius: '6px'                               
                                        },
                                        '& .MuiSvgIcon-root': {
                                            color: 'var(--color-icons)'
                                        }
                                    }
                                }
                            }}
                        />
                    </div>
                </CustomTooltip>
            </LocalizationProvider>
        </div>
    );
}

export default WaitSelect;

/** End of file WaitSelect.tsx */
