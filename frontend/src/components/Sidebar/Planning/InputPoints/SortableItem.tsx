/**
 * @file SortableItem.tsx
 * @brief Represents a single waypoint that can be reordered using drag-and-drop
 * @author Andrea Svitkova (xsvitka00)
 */

import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import { useEffect, useRef } from "react";
import { useSortable } from "@dnd-kit/sortable";
import {CSS} from '@dnd-kit/utilities';
import InputField from "./InputField/InputField";
import Suggestions from "./Suggestions/Suggestions";
import { useInput } from "../../../InputContext";
import { useSuggestionHandle } from "./Suggestions/SuggestionsHandle";
import CustomTooltip from '../../../CustomTooltip/CustomTooltip';
import { useTranslation } from 'react-i18next';

type SortableItemProps = {
    index: number;
    closeSidebar: () => void;
};

function SortableItem({
    index,
    closeSidebar
}: SortableItemProps) {
    const { t } = useTranslation();

    const {
        waypoints, setWaypoints,
        activeField,
        clearWaypoint
    } = useInput();

    const waypoint = waypoints[index];
    const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);    
    const {attributes, listeners, setNodeRef, transform, transition} = useSortable({
        id: waypoint.id,
    });

    const {
        loadSuggestionsFromStorage,
        fetchSuggestions, 
        setSuggestions, 
        handleKeyDown, 
        suggestions, 
        handleSuggestionClick, 
        highlightedIndex, resetHighlightedIndex
    } = useSuggestionHandle(index);

    const style: React.CSSProperties = {
        transform: CSS.Transform.toString(transform),
        transition
    };
  
    const handleWaypointChange = (index: number, value: string) => {
        setWaypoints(prev => {
            const newWaypoints = [...prev];
                newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: value,
                isActive: false
            };
            return newWaypoints;
        });

        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        if (value.length >= 1) {
            debounceTimeoutRef.current = setTimeout(() => {
                fetchSuggestions(value);
            }, 200);
        } else {
            loadSuggestionsFromStorage();
            clearWaypoint(index, false);
        }
    };

    useEffect(() => {
        if (activeField === index && waypoint.displayName.length === 0) {
            loadSuggestionsFromStorage();
        }
    }, [activeField, waypoint.displayName, index, loadSuggestionsFromStorage]);

    useEffect(() => {
        if (highlightedIndex >= 0 && suggestions.length > 0) {
            setWaypoints(prev => {
                const newWaypoints = [...prev];

                newWaypoints[index] = {
                    ...newWaypoints[index],
                    isPreview: true,
                    lat: suggestions[highlightedIndex].lat,
                    lon: suggestions[highlightedIndex].lon
                }
                return newWaypoints;
            });
        }
    }, [highlightedIndex, index, suggestions]);

    return (
        <div className="sortable-item" ref={setNodeRef} style={style}>
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
