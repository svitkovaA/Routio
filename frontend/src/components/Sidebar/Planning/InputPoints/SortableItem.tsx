/**
 * @file SortableItem.tsx
 * @brief Represents a single waypoint that can be reordered using drag-and-drop
 * @author Andrea Svitkova (xsvitka00)
 */

import { useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faGripVertical } from "@fortawesome/free-solid-svg-icons";
import { useSortable } from "@dnd-kit/sortable";
import {CSS} from '@dnd-kit/utilities';
import { API_BASE_URL } from "../../../config/config";
import { InputText } from "../../../types/types";
import InputField from "./InputField/InputField";
import Suggestions from "./Suggestions/Suggestions";
import { useInput } from "../../../InputContext";

type SortableItemProps = {
    index: number;
    closeSidebar: () => void;
};

function SortableItem({
    index,
    closeSidebar
}: SortableItemProps) {
    const {
        waypoints, setWaypoints,
        activeField,
        clearWaypoint
    } = useInput();

    const waypoint = waypoints[index];
    const [suggestions, setSuggestions] = useState<InputText[]>([]);
    const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);
    
    const {attributes, listeners, setNodeRef, transform, transition} = useSortable({
        id: waypoint.id,
    });

    const style: React.CSSProperties = {
        transform: CSS.Transform.toString(transform),
        transition,
        display: 'flex',
        alignItems: 'center',
        position: 'relative'
    };

    const fetchSuggestions = (query: string) => {
        fetch(`${API_BASE_URL}/geocode/name?q=${encodeURIComponent(query)}`)
            .then((res) => {
                if (!res.ok) throw new Error("Network response was not ok");
                    return res.json();
                }
            )
            .then((data: InputText[]) => setSuggestions(data))
            .catch(console.error);
    };
  
    const handleWaypointChange = (index: number, value: string) => {
        setWaypoints(prev => {
            const newWaypoints = [...prev];
                newWaypoints[index] = { 
                ...newWaypoints[index], 
                displayName: value 
            };
            return newWaypoints;
        });

        if (debounceTimeoutRef.current) {
            clearTimeout(debounceTimeoutRef.current);
        }

        if (value.length > 1) {
            debounceTimeoutRef.current = setTimeout(() => {
                fetchSuggestions(value);
            }, 200);
        } else {
            setSuggestions([]);
            clearWaypoint(index, false);
        }
    };
  
    const handleSuggestionClick = (suggestion: InputText) => {
        if (activeField === index) {
            const newWaypoints = [...waypoints];
            const parts = [
                suggestion.name,
                suggestion.street,
                suggestion.city,
            ].filter(Boolean);
            newWaypoints[index] = {
                lat: suggestion.lat,
                lon: suggestion.lon,
                displayName: parts.join(", "),
                isActive: true,
                id: waypoints[index].id
            };
            setWaypoints(newWaypoints);
            setSuggestions([]);
        }
    };
  
    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>, currentIndex: number) => {
        if (activeField !== index || currentIndex !== index) {
            return;
        }
    
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlightedIndex(
                highlightedIndex < suggestions.length - 1 ? highlightedIndex + 1 : 0
            );
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlightedIndex(
                highlightedIndex > 0 ? highlightedIndex - 1 : suggestions.length - 1
            );
        } else if (e.key === "Enter") {
            if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
                e.preventDefault();
                handleSuggestionClick(suggestions[highlightedIndex]);
                setHighlightedIndex(-1);
            }
        }
    };

    return (
        <div ref={setNodeRef} style={style}>
            <div
                {...attributes} 
                {...listeners} 
                className="drag-and-drop"
                tabIndex={-1}
            >
                <FontAwesomeIcon icon={faGripVertical} color="lightgray"/>
            </div>

            <InputField
                index={index}
                lastIndex={waypoints.length - 1}
                waypointsLength={waypoints.length}
                waypoint={waypoint}
                handleWaypointChange={handleWaypointChange}
                handleKeyDown={handleKeyDown}
                setSuggestions={setSuggestions}
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
