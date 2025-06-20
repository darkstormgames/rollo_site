import { VMState } from './vm/vm.state';
import { ServerState } from './server/server.state';

export interface AppState {
  vms: VMState;
  servers: ServerState;
}