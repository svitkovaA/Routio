/**
 * @file DragHandle.tsx
 * @brief Mobile drag controller for the sidebar component
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import type { PointerEventHandler } from "react";
import { useResult } from "../../Contexts/ResultContext";
import { useBackButtonClick } from "../Results/useBackButtonClick";
import "./DragHandle.css";

type DragHandleProps = {
    translateY: number;                                                     // Current vertical translation value
    setTranslateY: (value: number | ((prev: number) => number)) => void;    // Setter for vertical translation
    draggingRef: React.RefObject<boolean>;                                  // Reference indicating whether dragging is active
    setIsDragging: (value: boolean) => void;                                // Setter for dragging state
    maxDrag: number;                                                        // Maximum allowed drag distance for fully opened state
    sidebarOpen: boolean;                                                   // Indicates whether sidebar is currently open
    setSidebarOpen: (value: boolean) => void;                               // Setter controlling sidebar visibility
};

function DragHandle({ 
    translateY, 
    setTranslateY, 
    draggingRef,
    setIsDragging,
    maxDrag,
    sidebarOpen,
    setSidebarOpen
} : DragHandleProps) {
    // Stores pointer Y position at drag start
    const startY = useRef<number>(0);

    // Stores translateY value at drag start
    const startTranslate = useRef<number>(0);

    // Indicates whether pointer movement exceeded drag threshold
    const hasDragged = useRef<boolean>(false);

    // Determines whether click should trigger view navigation
    const clickable = useRef<boolean>(false);

    // Result context
    const { showSettings, setShowSettings, showResults } = useResult();

    // Back button click navigation
    const { backButtonClick } = useBackButtonClick();

    /**
     * Pointer release handler
     */
    useEffect(() => {
        const handleUp = () => {
            // Ignore if dragging was not active
            if (!draggingRef.current) {
                return;
            }

            // No drag detected, treat as click
            if (!hasDragged.current) {
                if (clickable.current) {
                    // Close settings
                    if (showSettings) {
                        setShowSettings(false);
                    } 
                    // Trigger back navigation from results to input form
                    else if (showResults) {
                        backButtonClick();
                    }

                    // When returning from settings or results set sidebar open
                    if (showSettings || showResults) {
                        setTranslateY(-maxDrag);
                        setSidebarOpen(true);
                    }
                }
            }
            // Drag detected
            else {
                // Sidebar openness in range (0,1)
                const openness = -translateY / maxDrag;
    
                // Handle opening/closing sidebar based on the openness variable
                if (sidebarOpen) {
                    if (openness < 0.95) {
                        setTranslateY(0);
                        setSidebarOpen(false);
                    } else {
                        setTranslateY(-maxDrag);
                    }
                } else {
                    if (openness > 0.05) {
                        setTranslateY(-maxDrag);
                        setSidebarOpen(true);
                    } else {
                        setTranslateY(0);
                    }
                }
            }

            // Reset drag state
            draggingRef.current = false;
            setIsDragging(false);
            hasDragged.current = false;
        };

        // Ensures release is handled even if pointer leaves the area
        window.addEventListener("pointerup", handleUp);
        window.addEventListener("pointercancel", handleUp);

        // Cleanup
        return () => {
            window.removeEventListener("pointerup", handleUp);
            window.removeEventListener("pointercancel", handleUp);
        };
    }, [translateY, 
        maxDrag, 
        sidebarOpen, 
        showSettings, 
        showResults, 
        backButtonClick, 
        draggingRef,
        setIsDragging,
        setShowSettings, 
        setSidebarOpen, 
        setTranslateY
    ]);

    /**
     * Initializes dragging
     * 
     * @param e Pointer event
     * @param left Indicates whether the left drag area was pressed
     */
    const onPointerDown = (e: React.PointerEvent<HTMLDivElement>, left: boolean) => {
        e.preventDefault();
        draggingRef.current = true;
        setIsDragging(true);
        hasDragged.current = false;
        clickable.current = left;
        startY.current = e.clientY;
        startTranslate.current = translateY;
        e.currentTarget.setPointerCapture(e.pointerId);
    };

    /**
     * Handles pointer movement during drag
     * 
     * @param e Pointer event
     */
    const onPointerMove: PointerEventHandler<HTMLDivElement> = (e) => {
        if (!draggingRef.current) {
            return;
        }

        const delta = e.clientY - startY.current;

        if (Math.abs(delta) > 10) {
            hasDragged.current = true;
        }

        if (!hasDragged.current) {
            return;
        }

        const clamped = Math.max(-maxDrag, Math.min(0, startTranslate.current + delta));

        setTranslateY(clamped);
    };

    /**
     * Toggles sidebar state on click
     * 
     * @param e Pointer event
     */
    const handleClick: PointerEventHandler<HTMLDivElement> = (e) => {
        setTranslateY(prev => (prev === 0 ? -maxDrag : 0));
        e.preventDefault();
        e.stopPropagation();
    };

    return (
        <div className="drag-sidebar">
            <div
                className="drag-inner-left"
                onPointerDown={(e) => onPointerDown(e, true)}
                onPointerMove={onPointerMove}
            />
            <div 
                className="drag-inner"
                onPointerDown={handleClick}
            />
            <div
                className="drag-inner-right"
                onPointerDown={(e) => onPointerDown(e, false)}
                onPointerMove={onPointerMove}
            />
        </div>
    );
};

export default DragHandle;

/** End of file DragHandle.tsx */
