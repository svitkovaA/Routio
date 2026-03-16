/**
 * @file InputPoints.tsx
 * @brief Component for managing waypoint input fields
 * @author Andrea Svitkova (xsvitka00)
 */

import React from "react";
import { useTranslation } from "react-i18next";
import SwapVertIcon from '@mui/icons-material/SwapVert';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, TouchSensor } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { restrictToVerticalAxis, restrictToParentElement} from '@dnd-kit/modifiers';
import AddPointIcon from "./AddPointIcon/AddPointIcon";
import SortableItem from "./SortableItem";
import LegPreferences from "./LegPreferences/LegPreferences";
import { useInput } from "../../../Contexts/InputContext";
import CustomTooltip from "../../../CustomTooltip/CustomTooltip";
import "./InputPoints.css";

type InputPointsProps = {
    closeSidebar: () => void;   // Callback used to close sidebar
}

function InputPoints({
    closeSidebar
}: InputPointsProps) {
    // Translation function
    const { t } = useTranslation();
    
    // User input context
    const {
        waypoints,
        legPreferences,
        onDragEnd,
        addWaypoint,
        swapWaypoints 
    } = useInput();

    // Drag sensors configuration
    const sensors = useSensors(
        useSensor(PointerSensor), 
        useSensor(TouchSensor)
    );

    return (
        <div className="input-wrapper">
            {/* Draggable elements wrapper */}
            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={onDragEnd}
                modifiers={[restrictToVerticalAxis, restrictToParentElement]}
            >
                {/* Reordering logic */}
                <SortableContext items={waypoints.map(w => w.id)} strategy={verticalListSortingStrategy}>
                    {waypoints.map((_, index) => (
                        <React.Fragment key={waypoints[index].id}>
                            {/* Waypoint input field */}
                            <SortableItem 
                                index={index}
                                closeSidebar={closeSidebar}
                            />
                            <div className={"input-buttons " + (waypoints.length > 2 && index < waypoints.length - 1 && legPreferences[index].open ? "leg-preferences-open" : "")}>
                                {/* Insert new waypoint after current index */}
                                <AddPointIcon 
                                    onClick={() => addWaypoint(index)} 
                                    render={index < waypoints.length - 1}
                                    disabled={waypoints.length >= 10}
                                />
                                {/* Leg transport configuration */}
                                <LegPreferences 
                                    render={index < waypoints.length - 1 && waypoints.length > 2}
                                    index={index}
                                />
                            </div>
                        </React.Fragment>
                    ))}
                </SortableContext>
            </DndContext>
            {/* Swap origin and destination when two waypoints exist */}
            {waypoints.length === 2 && (
                <CustomTooltip title={t("tooltips.inputForm.swapWaypoints")}>
                    <SwapVertIcon 
                        className="swap" 
                        onClick={swapWaypoints}
                        sx={{ color: 'var(--color-icons)' }}
                    />
                </CustomTooltip>
            )}
        </div>
    );
}

export default InputPoints;

/** End of file InputPoints.tsx */
