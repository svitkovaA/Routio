/**
 * @file WaitSelect.tsx
 * @brief Component for selecting wait time between locations
 * @author Andrea Svitkova (xsvitka00)
 */

import { useInput } from "../../../../../InputContext";
import { TimePicker } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { LocalizationProvider } from "@mui/x-date-pickers";
import dayjs from "dayjs";
import CustomTooltip from "../../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";

type WaitSelectProps = {
    index: number;
}

function WaitSelect({ index }: WaitSelectProps) {
    const { t } = useTranslation()
    const { legPreferences, setLegPreferences } = useInput();
    
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
