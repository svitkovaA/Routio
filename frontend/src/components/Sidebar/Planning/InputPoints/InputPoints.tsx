/**
 * @file InputPoints.tsx
 * @brief Displays component for managing multiple waypoint input fields with drag-and-drop reordering, adding and removing intermediate points, and editing leg preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import React from "react";
import { faRightLeft } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DndContext, closestCenter, PointerSensor, useSensor, useSensors, DragEndEvent, TouchSensor } from '@dnd-kit/core';
import { arrayMove, SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { restrictToVerticalAxis, restrictToParentElement} from '@dnd-kit/modifiers';
import { Waypoint, LegPreference } from '../../../types/types';
import AddPointIcon from "./AddPointIcon/AddPointIcon";
import SortableItem from "./SortableItem";
import LegPreferences from "./LegPreferences/LegPreferences";
import "./InputPoints.css";

type InputPointsProps = {
    waypoints: Waypoint[];
    setWaypoints: (value: Waypoint[] | ((prev: Waypoint[]) => Waypoint[])) => void;
    setMapSelectionIndex: (value: number) => void;
    closeSidebar: () => void;
    legPreferences: LegPreference[];
    setLegPreferences: (value: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    activeField: number | null;
    setActiveField: (value: number | null) => void;
    clearWaypoint: (index: number, clearDisplayName: boolean) => void;
    removeWaypoint: (currentIndex: number) => void;
}

function InputPoints({
    waypoints,
    setWaypoints,
    setMapSelectionIndex,
    closeSidebar,
    legPreferences,
    setLegPreferences,
    activeField,
    setActiveField,
    clearWaypoint,
    removeWaypoint
}: InputPointsProps) {
    const addWaypoint = (index: number) => {
        const newWaypoints = [...waypoints];
        newWaypoints.splice(index + 1, 0, {
            lat: 0,
            lon: 0,
            displayName: "",
            isActive: false,
            id: Math.random().toString(36).substring(2,9)
        });
        setWaypoints(newWaypoints);
        const newLegPreferences = [...legPreferences];
        newLegPreferences.splice(index + 1, 0, {
            mode: "transit,bicycle,walk",
            exact: true,
            open: false
        });
        setLegPreferences(newLegPreferences);
    };

    const sensors = useSensors(
        useSensor(PointerSensor), 
        useSensor(TouchSensor)
    );

    const onDragEnd = (event: DragEndEvent) => {
        const {active, over} = event;
        if (over && active.id !== over.id) {
            const oldIndex = waypoints.findIndex(w => w.id === active.id);
            const newIndex = waypoints.findIndex(w => w.id === over.id);
            setWaypoints(prev => arrayMove(prev, oldIndex, newIndex));
        }
    };

    const swapWaypoints = () => {
        if (waypoints.length === 2) {
            setWaypoints(prev => [prev[1], prev[0]]);
        }
    };

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
                                waypoints={waypoints}
                                setWaypoints={setWaypoints}
                                index={index}
                                setMapSelectionIndex={setMapSelectionIndex}
                                closeSidebar={closeSidebar}
                                activeField={activeField}
                                setActiveField={setActiveField}
                                setLegPreferences={setLegPreferences}
                                clearWaypoint={clearWaypoint}
                                removeWaypoint={removeWaypoint}
                            />
                            <div className={"input-buttons " + (waypoints.length > 2 && index < waypoints.length - 1 && legPreferences[index].open ? "leg-preferences-open" : "")}>
                                <AddPointIcon 
                                    onClick={() => addWaypoint(index)} 
                                    render={index < waypoints.length - 1}/>
                                <LegPreferences 
                                    render={index < waypoints.length - 1 && waypoints.length > 2}
                                    legPreferences={legPreferences}
                                    setLegPreferences={setLegPreferences}
                                    index={index}
                                />
                            </div>
                        </React.Fragment>
                    ))}
                </SortableContext>
            </DndContext>
            {waypoints.length === 2 && (
                <FontAwesomeIcon icon={faRightLeft} className="swap" onClick={swapWaypoints} color="gray"/>
            )}
        </div>
    );
}

export default InputPoints;

/** End of file InputPoints.tsx */
