import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { Server, ServerStatus } from '../../models/server/server.model';

export const serverActions = createActionGroup({
  source: 'Server',
  events: {
    // Loading servers
    'Load Servers': emptyProps(),
    'Load Servers Success': props<{ servers: Server[] }>(),
    'Load Servers Failure': props<{ error: Error }>(),
    
    // Selection
    'Select Server': props<{ id: string }>(),
    'Clear Selection': emptyProps(),
    
    // Real-time updates
    'Server Status Changed': props<{ id: number; status: ServerStatus }>(),
    'Server Registered': props<{ server: Server }>(),
    'Server Removed': props<{ id: number }>(),
  }
});