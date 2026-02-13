/**
 * @file LayerSelect.tsx
 * @brief Dropdown component for selecting the active map layer
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import LayersIcon from '@mui/icons-material/Layers';
import { useSettings } from "../../SettingsContext";
import { useLayers } from "./Layers";
import "./LayerSelect.css";

function LayerSelect() {
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

    return (
        <div className={"controls-select " + (window.innerWidth < 768)}>
            {/* Button opening the layer selection dropdown */}
            <button
                onBlur={() => setOpen(false)}
                className={"controls-button controls-button-layer " + (open ? "open" : "")}
                onClick={() => {
                    setOpen(!open);
                }}
            >
                <LayersIcon 
                    fontSize="small"
                    sx={{ color: 'var(--color-text-primary)' }}
                />
                <ExpandMoreIcon 
                    fontSize="small" 
                    className={open ? "rotate" : ""}
                    sx={{ 
                        color: 'var(--color-text-primary)'
                    }}
                />
            </button>

            {/* Dropdown menu with available map layers */}
            {open && (
                <div className="dropdown dropdown-layer">
                    {baseLayers.map((layer, index) => (
                        <div
                            key={layer.name}
                            className={"dropdown-item " + (index === selectedLayerIndex ? "selected" : "")}
                            onMouseDown={() => handleSelect(index)}
                        >
                            {layer.name}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default LayerSelect;

/** End of file LayerSelect.tsx */
