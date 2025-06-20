import { EntityState } from '@ngrx/entity';
import { Server } from '../../models/server/server.model';

export interface ServerState extends EntityState<Server> {
  selectedId: string | null;
  loading: boolean;
  error: Error | null;
  lastUpdated: string | null;
}

export const initialServerState: ServerState = {
  ids: [],
  entities: {},
  selectedId: null,
  loading: false,
  error: null,
  lastUpdated: null,
};