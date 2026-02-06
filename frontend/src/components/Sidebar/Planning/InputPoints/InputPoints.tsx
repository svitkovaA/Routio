/**
 * @file InputPoints.tsx
 * @brief Displays component for managing multiple waypoint input fields with drag-and-drop reordering, adding and removing intermediate points, and editing leg preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import React from "react";
import SwapVertIcon from '@mui/icons-material/SwapVert';
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, TouchSensor } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { restrictToVerticalAxis, restrictToParentElement} from '@dnd-kit/modifiers';
import AddPointIcon from "./AddPointIcon/AddPointIcon";
import SortableItem from "./SortableItem";
import LegPreferences from "./LegPreferences/LegPreferences";
import "./InputPoints.css";
import { useInput } from "../../../InputContext";

type InputPointsProps = {
    closeSidebar: () => void;
}

function InputPoints({
    closeSidebar
}: InputPointsProps) {
    const {
        waypoints,
        legPreferences,
        onDragEnd,
        addWaypoint,
        swapWaypoints 
    } = useInput();

    const sensors = useSensors(
        useSensor(PointerSensor), 
        useSensor(TouchSensor)
    );

    return (
        <div className="input-wrapper">
            <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={onDragEnd}
                modifiers={[restrictToVerticalAxis, restrictToParentElement]}
            >
                <SortableContext items={waypoints.map(w => w.id)} strategy={verticalListSortingStrategy}>
                    {waypoints.map((_, index) => (
                        <React.Fragment key={waypoints[index].id}>
                            <SortableItem 
                                index={index}
                                closeSidebar={closeSidebar}
                            />
                            <div className={"input-buttons " + (waypoints.length > 2 && index < waypoints.length - 1 && legPreferences[index].open ? "leg-preferences-open" : "")}>
                                <AddPointIcon 
                                    onClick={() => addWaypoint(index)} 
                                    render={index < waypoints.length - 1}
                                    disabled={waypoints.length >= 10}
                                />
                                <LegPreferences 
                                    render={index < waypoints.length - 1 && waypoints.length > 2}
                                    index={index}
                                />
                            </div>
                        </React.Fragment>
                    ))}
                </SortableContext>
            </DndContext>
            {waypoints.length === 2 && (
                <SwapVertIcon 
                    className="swap" 
                    onClick={swapWaypoints}
                    sx={{ color: 'var(--color-icons)' }}
                />
            )}
        </div>
    );
}

export default InputPoints;

/** End of file InputPoints.tsx */
