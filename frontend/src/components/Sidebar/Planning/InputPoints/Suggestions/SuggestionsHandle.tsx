/**
 * @file SuggestionsHandle.tsx
 * @brief Hook managing autocomplete suggestion logic for waypoint input fields
 * @author Andrea Svitkova (xsvitka00)
 */

import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { API_BASE_URL } from "../../../../config/config";
import type { Suggestion } from "../../../../types/types";
import { useInput } from "../../../../Contexts/InputContext";
import { loadEndWaypoints, loadMiddleWaypoints } from "../WaypointStorage";
import { useNotification } from "../../../../Contexts/NotificationContext";

/**
 * Hook for managing suggestion behavior for a specific waypoint index
 * 
 * @param index Index of waypoint in input list
 */
export function useSuggestionHandle(index: number) {
    // Translation function
    const { t } =useTranslation(); 

    // List of currently available suggestions
    const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

    // Index of currently highlighted suggestion
    const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

    // Notification context
    const { showNotification } = useNotification();

    // User input context
    const {
        waypoints, setWaypoints,
        activeField
    } = useInput();

    /**
     * Loads suggestions from localStorage
     */
    const loadSuggestionsFromStorage = useCallback(() => {
        if (index === 0 || index === waypoints.length - 1) {
            const endWaypoints = loadEndWaypoints();
            setSuggestions(endWaypoints);
        }
        else {
            const middle_waypoints = loadMiddleWaypoints();
            setSuggestions(middle_waypoints);
        }
    }, [index, waypoints.length]);

    /**
     * Fetches suggestions from backend geocoding API
     * 
     * @param query Input string
     */
    const fetchSuggestions = (query: string) => {
        fetch(`${API_BASE_URL}/geocode/name?q=${encodeURIComponent(query)}`)
            .then((res) => {
                if (!res.ok) throw new Error("Network response was not ok");
                    return res.json();
                }
            )
            .then((data: Suggestion[]) => {
                setSuggestions(data);
                setHighlightedIndex(-1);
            })
            .catch(() => {
                showNotification(t("warnings.photon"), "warning");
                console.error("Nominatim error");
            });
    };

    /**
     * Handles selection of suggestion
     * 
     * @param suggestion The selected suggestion
     */
    const handleSuggestionClick = (suggestion: Suggestion) => {
        if (activeField === index) {
            const newWaypoints = [...waypoints];

            newWaypoints[index] = {
                lat: suggestion.lat,
                lon: suggestion.lon,
                displayName: suggestion.name,
                isActive: true,
                isPreview: false,
                id: waypoints[index].id,
                bikeStationId: null,
                origin: null,
                isBus: suggestion.isBus,
                isTrain: suggestion.isTrain
            };
            setWaypoints(newWaypoints);
            setSuggestions([]);
            setHighlightedIndex(-1);
        }
    };

    /**
     * Handles keyboard navigation in suggestion list
     */
    const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>, currentIndex: number) => {
        if (activeField !== index || currentIndex !== index) {
            return;
        }
    
        // Move selection down
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlightedIndex(
                highlightedIndex < suggestions.length - 1 ? highlightedIndex + 1 : 0
            );
        }
        // Move selection up
        else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlightedIndex(
                highlightedIndex > 0 ? highlightedIndex - 1 : suggestions.length - 1
            );
        }
        // Confirm selection
        else if (e.key === "Enter") {
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

/** End of file SuggestionsHandle.tsx */
