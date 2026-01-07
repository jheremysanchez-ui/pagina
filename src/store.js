import { configureStore } from '@reduxjs/toolkit';

import rootReducer from './redux/reducers'; 


const initialState = {};

const store = configureStore({
    reducer: {
        root: rootReducer
    },
    preloadedState: initialState
});


export default store;
