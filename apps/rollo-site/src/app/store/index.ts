import { isDevMode } from '@angular/core';
import { ActionReducerMap, MetaReducer } from '@ngrx/store';
import { AppState } from './app.state';
import { vmReducer } from './vm/vm.reducer';
import { serverReducer } from './server/server.reducer';

export const reducers: ActionReducerMap<AppState> = {
  vms: vmReducer,
  servers: serverReducer,
};

export const metaReducers: MetaReducer<AppState>[] = isDevMode() ? [] : [];