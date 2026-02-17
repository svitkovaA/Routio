/**
 * @file index.tsx
 * @brief Entry point of the application, renders the root component
 * @author Andrea Svitkova (xsvitka00)
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import "./i18n";
import App from './App';
import { SettingsProvider } from './components/SettingsContext';
import { InputProvider } from './components/InputContext';
import { ResultProvider } from './components/ResultContext';
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

/** End of file index.tsx */
