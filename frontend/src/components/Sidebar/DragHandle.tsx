import { PointerEventHandler, useEffect, useRef } from "react";

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
    const hasDragged = useRef(false);

    useEffect(() => {
        const handleUp = () => {
            if (!dragging.current) return;

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
            dragging.current = false;
            hasDragged.current = false;
        };

        window.addEventListener("pointerup", handleUp);
        window.addEventListener("pointercancel", handleUp);

        return () => {
            window.removeEventListener("pointerup", handleUp);
            window.removeEventListener("pointercancel", handleUp);
        };
    }, [translateY, maxDrag, sidebarOpen]);


    const onPointerDown: PointerEventHandler<HTMLDivElement> = (e) => {
        dragging.current = true;
        hasDragged.current = false;
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
        <div
            id="drag-sidebar"
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
        >
            <div 
                className="drag-inner"
                onPointerDown={handleClick}
            />
        </div>
    );
};

export default DragHandle;
