/**
 * @file LayerSelect.tsx
 * @brief Dropdown component for selecting the active map layer
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import LayersIcon from '@mui/icons-material/Layers';
import { useSettings } from "../../SettingsContext";
import { useLayers } from "./Layers";
import "./LayerSelect.css";


type LayerSelectProps = {
    showInfo: boolean;
    closeInfo: () => void;
};

function LayerSelect({ 
    showInfo,
    closeInfo
}: LayerSelectProps) {
    // Context for storing the selected map layer to the settings
    const { selectedLayerIndex, setSelectedLayerIndex } = useSettings();

    // State controlling the visibility of the dropdown menu
    const [open, setOpen] = useState<boolean>(false);

    // Available base map layers
    const { baseLayers } = useLayers();

    /**
     * Handles selection of the map layer 
     * @param index Index of the selected layer
     */
    const handleSelect = (index: number) => {
        setSelectedLayerIndex(index);
        setOpen(false);
    };

    // State to trigger rerender on window resize
    const [_, setCloseDropdown] = useState<boolean>(true);

    /**
     * When the information panel is visible on small screens, 
     * the layer selector is hidden
     */
    useEffect(() => {
        const handleResize = () => setCloseDropdown(!(window.innerWidth < 769 && showInfo));
        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [showInfo]);
    

    return (
    <div className={"controls-select " + (window.innerWidth < 769 && showInfo ? "hidden" : "")}>
        {/* Button opening the layer selection dropdown */}
        <button
            onBlur={() => setOpen(false)}
            className={"controls-button controls-button-layer " + (open ? "open" : "")}
            onClick={() => {
                if (showInfo) {
                    closeInfo();
                }
                else {
                    setOpen(!open);
                }
            }}
        >
            <LayersIcon fontSize="small"/>
            <ExpandMoreIcon 
                fontSize="small" 
                className={open ? "rotate" : ""} 
            />
        </button>

        {/* Dropdown menu with available map layers */}
        {open && (
            <div className="dropdown dropdown-layer">
                {baseLayers
                    .map((layer, index) => (
                        <div
                            key={layer.name}
                            className={"dropdown-item " + (index === selectedLayerIndex ? "selected" : "")}
                            onMouseDown={() => handleSelect(index)}
                        >
                            {layer.name}
                        </div>
                    ))
                }
            </div>
        )}
    </div>
    );
}

export default LayerSelect;

/** End of file LayerSelect.tsx */
