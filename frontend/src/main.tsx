import React from 'react';
import ReactDOM from 'react-dom/client';
import "./i18n";
import App from './App';
import { SettingsProvider } from './components/Contexts/SettingsContext'
import { InputProvider } from './components/Contexts/InputContext'
import { ResultProvider } from './components/Contexts/ResultContext'
import './index.css'
import { NotificationProvider } from './components/Contexts/NotificationContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <NotificationProvider>
            <ResultProvider>
                <InputProvider>
                    <SettingsProvider>
                        <App />
                    </SettingsProvider>
                </InputProvider>
            </ResultProvider>
        </NotificationProvider>
    </React.StrictMode>
);

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        // The worker must live under the app prefix (BASE_URL, e.g. "/routio/").
        navigator.serviceWorker.register(`${import.meta.env.BASE_URL}service-worker.js`);
    });
}
