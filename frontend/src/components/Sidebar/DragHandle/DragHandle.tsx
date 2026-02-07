import { PointerEventHandler, useEffect, useRef } from "react";
import "./DragHandle.css";
import { useResult } from "../../ResultContext";
import { useBackButtonClick } from "../Results/useBackButtonClick";

type DragHandleProps = {
    translateY: number;
    setTranslateY: (value: number | ((prev: number) => number)) => void;
    dragging: React.RefObject<boolean>;
    maxDrag: number;
    sidebarOpen: boolean;
    setSidebarOpen: (value: boolean) => void;
};

function DragHandle({ 
    translateY, 
    setTranslateY, 
    dragging,
    maxDrag,
    sidebarOpen,
    setSidebarOpen
} : DragHandleProps) {
    const startY = useRef<number>(0);
    const startTranslate = useRef<number>(0);
    const hasDragged = useRef<boolean>(false);
    const clickable = useRef<boolean>(false);

    const { showSettings, setShowSettings, showResults } = useResult();
    const { backButtonClick } = useBackButtonClick();

    useEffect(() => {
        const handleUp = () => {
            if (!dragging.current) return;

            if (!hasDragged.current) {
                if (clickable.current) {
                    if (showSettings) {
                        setShowSettings(false);
                    } else if (showResults) {
                        backButtonClick();
                    }
                    if (showSettings || showResults) {
                        setTranslateY(-maxDrag);
                        setSidebarOpen(true);
                    }
                }
            } else {
                const openness = -translateY / maxDrag;
    
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
            dragging.current = false;
            hasDragged.current = false;
        };

        window.addEventListener("pointerup", handleUp);
        window.addEventListener("pointercancel", handleUp);

        return () => {
            window.removeEventListener("pointerup", handleUp);
            window.removeEventListener("pointercancel", handleUp);
        };
    }, [translateY, maxDrag, sidebarOpen, showSettings, showResults, backButtonClick]);


    const onPointerDown = (e: React.PointerEvent<HTMLDivElement>, left: boolean) => {
        e.preventDefault();
        dragging.current = true;
        hasDragged.current = false;
        clickable.current = left;
        startY.current = e.clientY;
        startTranslate.current = translateY;
        e.currentTarget.setPointerCapture(e.pointerId);
    };

    const onPointerMove: PointerEventHandler<HTMLDivElement> = (e) => {
        if (!dragging.current) return;

        const delta = e.clientY - startY.current;

        if (Math.abs(delta) > 10) {
            hasDragged.current = true;
        }

        if (!hasDragged.current) return;

        const clamped = Math.max(-maxDrag, Math.min(0, startTranslate.current + delta));

        setTranslateY(clamped);
    };

    const handleClick: PointerEventHandler<HTMLDivElement> = (e) => {
        setTranslateY(prev => (prev === 0 ? -maxDrag : 0));
        e.preventDefault();
        e.stopPropagation();
    };

    return (
        <div id="drag-sidebar">
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
