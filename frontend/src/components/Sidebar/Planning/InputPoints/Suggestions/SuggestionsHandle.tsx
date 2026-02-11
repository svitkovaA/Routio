import { useCallback, useState } from "react";
import { API_BASE_URL } from "../../../../config/config";
import { InputText, StoredWaypoint } from "../../../../types/types";
import { useInput } from "../../../../InputContext";
import { loadDestination, loadMiddleWaypoints, loadOrigin } from "../WaypointStorage";

export function useSuggestionHandle(index: number) {
    const [suggestions, setSuggestions] = useState<InputText[]>([]);
    const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

    const {
        waypoints, setWaypoints,
        activeField
    } = useInput();

    const transformStored = (stored: StoredWaypoint[]) => {
        return stored.map((s) => ({
            ...s,
            street: "",
            city: ""
        }));
    }

    const loadSuggestionsFromStorage = useCallback(() => {
        if (index === 0) {
            const origin = loadOrigin();
            setSuggestions(transformStored(origin));
        }
        else if (index === waypoints.length - 1) {
            const destination = loadDestination();
            setSuggestions(transformStored(destination));
        }
        else {
            const middle_waypoints = loadMiddleWaypoints();
            setSuggestions(transformStored(middle_waypoints));
        }
    }, [index, waypoints.length]);

    const fetchSuggestions = (query: string) => {
        fetch(`${API_BASE_URL}/geocode/name?q=${encodeURIComponent(query)}`)
            .then((res) => {
                if (!res.ok) throw new Error("Network response was not ok");
                    return res.json();
                }
            )
            .then((data: InputText[]) => {
                setSuggestions(data);
                setHighlightedIndex(-1);
            })
            .catch(console.error);
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
                isPreview: false,
                id: waypoints[index].id
            };
            setWaypoints(newWaypoints);
            setSuggestions([]);
            setHighlightedIndex(-1);
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
    
    return { 
        loadSuggestionsFromStorage, 
        suggestions, setSuggestions,
        fetchSuggestions, 
        handleSuggestionClick, 
        handleKeyDown, 
        highlightedIndex, resetHighlightedIndex: () => setHighlightedIndex(-1)
    };
}
