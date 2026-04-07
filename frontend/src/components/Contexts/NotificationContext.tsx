/* eslint-disable react-refresh/only-export-components */
/**
 * @file NotificationContext.tsx
 * @brief Provides global notification system for success messages, warnings and errors
 * @author Andrea Svitkova (xsvitka00)
 */

import { createContext, useContext, useState } from "react";
import Snackbar from "@mui/material/Snackbar";
import type { SnackbarCloseReason } from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";

// Allowed notification severity levels
type Severity = "success" | "error" | "warning";

type NotificationContextType = {
    showNotification: (message: string, severity: Severity) => void;
};

const NotificationContext = createContext<NotificationContextType | null>(null);

export function NotificationProvider({ children }: { children: React.ReactNode }) {
    // Controls Snackbar visibility
    const [open, setOpen] = useState(false);

    // Current notification message
    const [message, setMessage] = useState("");

    // Current notification severity level
    const [severity, setSeverity] = useState<Severity>("success");

    // Displays a notification with given message and severity
    const showNotification = (msg: string, sev: Severity) => {
        setMessage(msg);
        setSeverity(sev);
        setOpen(true);
    };

    // Handles Snackbar close events
    const handleClose = (_?: React.SyntheticEvent | Event, reason?: SnackbarCloseReason) => {
        // Prevent closing when clicking outside
        if (reason === "clickaway") {
            return;
        }
        setOpen(false);
    };

    return (
        <NotificationContext.Provider value={{ showNotification }}>
            {children}

            <Snackbar
                className=""
                open={open}
                autoHideDuration={5000}
                onClose={handleClose}
                anchorOrigin={{ vertical: "top", horizontal: "left" }}
                sx={{
                    top: {
                        xs: "20px",
                        sm: "19px"
                    },
                    maxWidth: {
                        xs: "calc(100% - 250px)",
                        sm: "min(calc(100% - 440px - 230px), 400px)"
                    },
                    minWidth: {
                        sm: "200px !important"
                    },
                    left: {
                        xs: "90px",
                        sm: "max(440px, calc(50% - 200px))"
                    },
                    zIndex: 1300
                }}
            >
                <Alert
                    severity={severity}
                    onClose={handleClose}
                    sx={{
                        width: "100%",
                        backgroundColor:
                            severity === "success" ? "#e6f4f2" : severity === "error" ? "#fdecea" : severity === "warning" ? "#fff4e5" : undefined,
                        color:
                            severity === "success" ? "#057f73" : severity === "error" ? "#7a3b3b" : severity === "warning" ? "#98793e" : undefined,
                        border: "1px solid",
                        borderColor:    
                            severity === "success" ? "#057f73" : severity === "error" ? "#7a3b3b" : severity === "warning" ? "#98793e" : undefined,
                    }}
                >
                    {message}
                </Alert>
            </Snackbar>
        </NotificationContext.Provider>
    );
}

export function useNotification() {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error("useNotification must be used within NotificationProvider");
    }
    return context;
}

/** End of file NotificationContext.tsx */
