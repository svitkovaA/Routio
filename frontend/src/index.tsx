/**
 * @file index.tsx
 * @brief Entry point of the application, renders the root component
 * @author Andrea Svitkova (xsvitka00)
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { SettingsProvider } from './components/SettingsContext';
import { InputProvider } from './components/InputContext';
import "./i18n";
import './index.css';
import { ResultProvider } from './components/ResultContext';

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);
root.render(
    <React.StrictMode>
        <InputProvider>
            <ResultProvider>
                <SettingsProvider>
                    <App />
                </SettingsProvider>
            </ResultProvider>
        </InputProvider>
    </React.StrictMode>
);

/** End of file index.tsx */
