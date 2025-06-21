import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';
import { map, catchError, switchMap, tap, withLatestFrom, concatMap } from 'rxjs/operators';

import { VMService } from '../../services/vm/vm.service';
import { WebSocketService } from '../../services/websocket/websocket.service';
import { vmActions } from './vm.actions';
import { AppState } from '../app.state';
import { selectVMById } from './vm.selectors';
import { WebSocketEventType } from '../../models/websocket/websocket.model';

@Injectable()
export class VMEffects {

  constructor(
    private actions$: Actions,
    private store: Store<AppState>,
    private vmService: VMService,
    private webSocketService: WebSocketService
  ) { console.log('VMEffects initialized actions$', actions$); }

  // // Load VMs
  // loadVMs$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.loadVMs),
  //     switchMap(({ filters }) =>
  //       this.vmService.getVMs(filters).pipe(
  //         map(response => vmActions.loadVMsSuccess({ vms: response.vms })),
  //         catchError(error => of(vmActions.loadVMsFailure({ error })))
  //       )
  //     )
  //   )
  // );

  // // Create VM
  // createVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.createVM),
  //     switchMap(({ vmData }) =>
  //       this.vmService.createVM(vmData).pipe(
  //         map(vm => vmActions.createVMSuccess({ vm })),
  //         catchError(error => of(vmActions.createVMFailure({ error })))
  //       )
  //     )
  //   )
  // );

  // // Update VM
  // updateVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.updateVM),
  //     concatMap(({ id, changes }) => {
  //       // Optimistic update
  //       this.store.dispatch(vmActions.updateVMOptimistic({ id, changes }));     
  //       return this.vmService.updateVM(id, changes).pipe(
  //         map(vm => vmActions.updateVMSuccess({ vm })),
  //         catchError(error => {
  //           // Revert optimistic update on error
  //           this.store.dispatch(vmActions.revertVMUpdate({ id }));
  //           return of(vmActions.updateVMFailure({ id, error }));
  //         })
  //       );
  //     })
  //   )
  // );

  // // Delete VM
  // deleteVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.deleteVM),
  //     switchMap(({ id }) =>
  //       this.vmService.deleteVM(id).pipe(
  //         map(() => vmActions.deleteVMSuccess({ id })),
  //         catchError(error => of(vmActions.deleteVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // Start VM
  // startVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.startVM),
  //     switchMap(({ id }) =>
  //       this.vmService.startVM(id).pipe(
  //         switchMap(() =>
  //           // Get updated VM data
  //           this.vmService.getVM(id).pipe(
  //             map(vm => vmActions.startVMSuccess({ id, vm })),
  //             catchError(error => of(vmActions.startVMFailure({ id, error })))
  //           )
  //         ),
  //         catchError(error => of(vmActions.startVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // Stop VM
  // stopVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.stopVM),
  //     switchMap(({ id, force }) =>
  //       this.vmService.stopVM(id, force).pipe(
  //         switchMap(() =>
  //           // Get updated VM data
  //           this.vmService.getVM(id).pipe(
  //             map(vm => vmActions.stopVMSuccess({ id, vm })),
  //             catchError(error => of(vmActions.stopVMFailure({ id, error })))
  //           )
  //         ),
  //         catchError(error => of(vmActions.stopVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // Restart VM
  // restartVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.restartVM),
  //     switchMap(({ id, force }) =>
  //       this.vmService.restartVM(id, force).pipe(
  //         switchMap(() =>
  //           // Get updated VM data
  //           this.vmService.getVM(id).pipe(
  //             map(vm => vmActions.restartVMSuccess({ id, vm })),
  //             catchError(error => of(vmActions.restartVMFailure({ id, error })))
  //           )
  //         ),
  //         catchError(error => of(vmActions.restartVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // Pause VM
  // pauseVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.pauseVM),
  //     switchMap(({ id }) =>
  //       this.vmService.pauseVM(id).pipe(
  //         switchMap(() =>
  //           // Get updated VM data
  //           this.vmService.getVM(id).pipe(
  //             map(vm => vmActions.pauseVMSuccess({ id, vm })),
  //             catchError(error => of(vmActions.pauseVMFailure({ id, error })))
  //           )
  //         ),
  //         catchError(error => of(vmActions.pauseVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // Resume VM
  // resumeVM$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(vmActions.resumeVM),
  //     switchMap(({ id }) =>
  //       this.vmService.resumeVM(id).pipe(
  //         switchMap(() =>
  //           // Get updated VM data
  //           this.vmService.getVM(id).pipe(
  //             map(vm => vmActions.resumeVMSuccess({ id, vm })),
  //             catchError(error => of(vmActions.resumeVMFailure({ id, error })))
  //           )
  //         ),
  //         catchError(error => of(vmActions.resumeVMFailure({ id, error })))
  //       )
  //     )
  //   )
  // );

  // // WebSocket VM status updates
  // vmStatusUpdates$ = createEffect(() =>
  //   this.webSocketService.messages$.pipe(
  //     map(message => message.data),
  //     switchMap(data => {
  //       switch (data.type) {
  //         case WebSocketEventType.VM_STATUS_CHANGED:
  //           return of(vmActions.vMStatusChanged({ 
  //             id: data.vm_id, 
  //             status: data.new_status 
  //           }));
  //         case WebSocketEventType.VM_CREATED:
  //           return of(vmActions.vMCreatedRealTime({ vm: data.vm }));
  //         case WebSocketEventType.VM_DELETED:
  //           return of(vmActions.vMDeletedRealTime({ id: data.vm_id }));
  //         case WebSocketEventType.VM_METRICS_UPDATE:
  //           return of(vmActions.vMMetricsUpdated({ 
  //             id: data.vm_id, 
  //             metrics: data.metrics 
  //           }));
  //         default:
  //           return of();
  //       }
  //     }),
  //     catchError(error => {
  //       console.error('WebSocket VM update error:', error);
  //       return of();
  //     })
  //   )
  // );

  // // Log successful operations
  // logOperations$ = createEffect(() =>
  //   this.actions$.pipe(
  //     ofType(
  //       vmActions.createVMSuccess,
  //       vmActions.updateVMSuccess,
  //       vmActions.deleteVMSuccess,
  //       vmActions.startVMSuccess,
  //       vmActions.stopVMSuccess,
  //       vmActions.restartVMSuccess,
  //       vmActions.pauseVMSuccess,
  //       vmActions.resumeVMSuccess
  //     ),
  //     tap(action => {
  //       console.log('VM operation completed:', action.type);
  //     })
  //   ),
  //   { dispatch: false }
  // );
}