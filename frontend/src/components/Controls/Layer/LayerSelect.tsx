/**
 * @file LayerSelect.tsx
 * @brief Layer selection dropdown component to switch between available map layers
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleDown, faLayerGroup } from "@fortawesome/free-solid-svg-icons";
import { useLayers } from "./Layers";
import "./LayerSelect.css";
import { useSettings } from "../../SettingsContext";


type LayerSelectProps = {
    showInfo: boolean;
    closeInfo: () => void;
};

function LayerSelect({ 
    showInfo,
    closeInfo
}: LayerSelectProps) {
    const { selectedLayerIndex, setSelectedLayerIndex } = useSettings();

    const [open, setOpen] = useState<boolean>(false);
    const { baseLayers } = useLayers();

    const handleSelect = (index: number) => {
        setSelectedLayerIndex(index);
        setOpen(false);
    };

    const [_, setCloseDropdown] = useState<boolean>(true);
    useEffect(() => {
        const handleResize = () => setCloseDropdown(!(window.innerWidth < 769 && showInfo));
        handleResize();

        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [showInfo]);
    

    return (
    <div className={"controls-select " + (window.innerWidth < 769 && showInfo ? "hidden" : "")}>
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
            <FontAwesomeIcon icon={faLayerGroup} />
            <FontAwesomeIcon icon={faAngleDown} className={open ? "rotate" : ""} />
        </button>

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
