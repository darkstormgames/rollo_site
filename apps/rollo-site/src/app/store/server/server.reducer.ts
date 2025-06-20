import { createReducer, on } from '@ngrx/store';
import { createEntityAdapter, EntityAdapter } from '@ngrx/entity';
import { Server } from '../../models/server/server.model';
import { ServerState, initialServerState } from './server.state';
import { serverActions } from './server.actions';

export const serverAdapter: EntityAdapter<Server> = createEntityAdapter<Server>({
  selectId: (server: Server) => server.id,
  sortComparer: (a: Server, b: Server) => a.hostname.localeCompare(b.hostname),
});

const serverEntityState = serverAdapter.getInitialState(initialServerState);

export const serverReducer = createReducer(
  serverEntityState,
  
  // Load servers
  on(serverActions.loadServers, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  
  on(serverActions.loadServersSuccess, (state, { servers }) => 
    serverAdapter.setAll(servers, {
      ...state,
      loading: false,
      error: null,
      lastUpdated: new Date().toISOString(),
    })
  ),
  
  on(serverActions.loadServersFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  
  // Selection
  on(serverActions.selectServer, (state, { id }) => ({
    ...state,
    selectedId: id,
  })),
  
  on(serverActions.clearSelection, (state) => ({
    ...state,
    selectedId: null,
  })),
  
  // Real-time updates
  on(serverActions.serverStatusChanged, (state, { id, status }) =>
    serverAdapter.updateOne(
      { id, changes: { status, updated_at: new Date().toISOString() } },
      state
    )
  ),
  
  on(serverActions.serverRegistered, (state, { server }) =>
    serverAdapter.addOne(server, state)
  ),
  
  on(serverActions.serverRemoved, (state, { id }) =>
    serverAdapter.removeOne(id, {
      ...state,
      selectedId: state.selectedId === id.toString() ? null : state.selectedId,
    })
  )
);