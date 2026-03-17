/**
 * @file index.tsx
 * @brief Entry point of the application, renders the root component
 * @author Andrea Svitkova (xsvitka00)
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import "./i18n";
import App from './App';
import { SettingsProvider } from './components/Contexts/SettingsContext';
import { InputProvider } from './components/Contexts/InputContext';
import { ResultProvider } from './components/Contexts/ResultContext';
import './index.css';

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);
root.render(
    <React.StrictMode>
        <ResultProvider>
            <InputProvider>
                <SettingsProvider>
                    <App />
                </SettingsProvider>
            </InputProvider>
        </ResultProvider>
    </React.StrictMode>
);

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/service-worker.js")
    });
}

/** End of file index.tsx */
