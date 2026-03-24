/**
 * @file SortableItem.tsx
 * @brief Represents a single draggable waypoint input field
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import { useTranslation } from 'react-i18next';
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import { useSortable } from "@dnd-kit/sortable";
import {CSS} from '@dnd-kit/utilities';
import InputField from "./InputField/InputField";
import Suggestions from "./Suggestions/Suggestions";
import { useInput } from "../../../Contexts/InputContext";
import { useSuggestionHandle } from "./Suggestions/SuggestionsHandle";
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';

type SortableItemProps = {
    index: number;                  // Index of waypoint in the list
    closeSidebar: () => void;       // Callback used to close sidebar
};

function SortableItem({
    index,
    closeSidebar
}: SortableItemProps) {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const {
        waypoints, setWaypoints,
        activeField,
        clearWaypoint
    } = useInput();

    // Currently processed waypoint
    const waypoint = waypoints[index];

    // Debounce timeout for suggestion fetching
    const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);  
    
    // Enable drag and drop behavior using dnd-kit
    const {
        attributes, listeners, setNodeRef, transform, transition
    } = useSortable({ id: waypoint.id, });

    // Hook for suggestion logic
    const {
        loadSuggestionsFromStorage,
        fetchSuggestions, 
        setSuggestions, 
        handleKeyDown, 
        suggestions, 
        handleSuggestionClick, 
        highlightedIndex, resetHighlightedIndex
    } = useSuggestionHandle(index);

    // Apply drag transform styles
    const style: React.CSSProperties = {
        transform: CSS.Transform.toString(transform),
        transition
    };
  
    /**
     * Handles user input changes in waypoint field
     * 
     * @param index Index of modified waypoint
     * @param value New input value
     */
    const handleWaypointChange = (index: number, value: string) => {
        // Update waypoint display name
        setWaypoints(prev => {
            const newWaypoints = [...prev];
                newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: value,
                isActive: false,
                bikeStationId: null,
                origin: null
            };
            return newWaypoints;
        });

        // Clear existing debounce timeout
        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        // Fetch suggestions with debounce
        if (value.length >= 1) {
            debounceTimeoutRef.current = setTimeout(() => {
                fetchSuggestions(value);
            }, 200);
        }
        // Load suggestions from local storage
        else {
            loadSuggestionsFromStorage();
            clearWaypoint(index, false);
        }
    };

    /**
     * Load suggestions from local storage when input field becomes active and empty
     */
    useEffect(() => {
        if (activeField === index && waypoint.displayName.length === 0) {
            loadSuggestionsFromStorage();
        }
    }, [activeField, waypoint.displayName, index, loadSuggestionsFromStorage]);

    /**
     * Preview of highlighted suggestion, temporarily updates waypoint coordinates
     */
    useEffect(() => {
        if (highlightedIndex >= 0 && suggestions.length > 0) {
            setWaypoints(prev => {
                const newWaypoints = [...prev];

                newWaypoints[index] = {
                    ...newWaypoints[index],
                    // Mark waypoint as preview state
                    isPreview: true,
                    // Temporarily apply highlighted suggestion coordinates
                    lat: suggestions[highlightedIndex].lat,
                    lon: suggestions[highlightedIndex].lon,
                    bikeStationId: null,
                    origin: null
                }
                return newWaypoints;
            });
        }
    }, [highlightedIndex, index, suggestions, setWaypoints]);

    return (
        <div className="sortable-item" ref={setNodeRef} style={style}>
            {/* Drag icon */}
            <div
                {...attributes} 
                {...listeners} 
                className="drag-and-drop"
                tabIndex={-1}
            >
                <CustomTooltip title={t("tooltips.inputForm.dragAndDrop")}>
                    <DragIndicatorIcon sx={{ color: 'var(--color-icons)' }}/>
                </CustomTooltip>
            </div>

            {/* Waypoint input field */}
            <InputField
                index={index}
                lastIndex={waypoints.length - 1}
                waypointsLength={waypoints.length}
                waypoint={waypoint}
                handleWaypointChange={handleWaypointChange}
                handleKeyDown={handleKeyDown}
                suggestions={suggestions}
                setSuggestions={setSuggestions}
                highlightedIndex={highlightedIndex}
                resetHighlightedIndex={resetHighlightedIndex}
                closeSidebar={closeSidebar}
            />

            {/* Autocomplete suggestions list */}
            <Suggestions
                suggestions={suggestions}
                handleSuggestionClick={handleSuggestionClick}
                highlightedIndex={highlightedIndex}
                render={activeField === index && suggestions.length > 0}
            />
        </div>
    );
};

export default SortableItem;

/** End of file SortableItem.tsx */
