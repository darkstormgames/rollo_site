import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { DataTableComponent, DataTableColumn, DataTableAction, DataTableConfig } from './data-table.component';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';

describe('DataTableComponent', () => {
  let component: DataTableComponent;
  let fixture: ComponentFixture<DataTableComponent>;

  const mockData = [
    { id: 1, name: 'Item 1', status: 'active', count: 10 },
    { id: 2, name: 'Item 2', status: 'inactive', count: 5 },
    { id: 3, name: 'Item 3', status: 'active', count: 15 }
  ];

  const mockColumns: DataTableColumn[] = [
    { key: 'id', label: 'ID', sortable: true, type: 'number' },
    { key: 'name', label: 'Name', sortable: true, searchable: true },
    { key: 'status', label: 'Status', searchable: true },
    { key: 'count', label: 'Count', sortable: true, type: 'number' }
  ];

  const mockActions: DataTableAction[] = [
    {
      label: 'Edit',
      icon: '✏️',
      action: jasmine.createSpy('editAction'),
      class: 'btn-primary'
    },
    {
      label: 'Delete',
      icon: '🗑️',
      action: jasmine.createSpy('deleteAction'),
      class: 'btn-danger',
      disabled: (row) => row.status === 'inactive'
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataTableComponent, FormsModule, LoadingSpinnerComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(DataTableComponent);
    component = fixture.componentInstance;
    
    component.data = mockData;
    component.columns = mockColumns;
    component.actions = mockActions;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with default config', () => {
    component.ngOnInit();
    
    expect(component.config.pageSize).toBe(10);
    expect(component.config.showPagination).toBeTrue();
    expect(component.config.showSearch).toBeTrue();
    expect(component.config.striped).toBeTrue();
    expect(component.config.responsive).toBeTrue();
  });

  it('should filter data correctly', () => {
    component.ngOnInit();
    fixture.detectChanges();
    
    component.searchTerm = 'Item 1';
    component.onSearch();
    
    expect(component.filteredData.length).toBe(1);
    expect(component.filteredData[0].name).toBe('Item 1');
  });

  it('should sort data correctly', () => {
    component.ngOnInit();
    fixture.detectChanges();
    
    component.onSort('count');
    
    expect(component.sortColumn).toBe('count');
    expect(component.sortDirection).toBe('asc');
    expect(component.filteredData[0].count).toBe(5);
    expect(component.filteredData[2].count).toBe(15);
  });

  it('should toggle sort direction', () => {
    component.ngOnInit();
    fixture.detectChanges();
    
    component.onSort('count');
    expect(component.sortDirection).toBe('asc');
    
    component.onSort('count');
    expect(component.sortDirection).toBe('desc');
    expect(component.filteredData[0].count).toBe(15);
  });

  it('should handle pagination correctly', () => {
    const largeData = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `Item ${i + 1}`,
      status: i % 2 === 0 ? 'active' : 'inactive',
      count: i + 1
    }));
    
    component.data = largeData;
    component.config.pageSize = 10;
    component.ngOnInit();
    fixture.detectChanges();
    
    expect(component.paginatedData.length).toBe(10);
    expect(component.getTotalPages()).toBe(3);
    
    component.goToPage(2);
    expect(component.currentPage).toBe(2);
    expect(component.paginatedData.length).toBe(10);
    
    component.goToPage(3);
    expect(component.currentPage).toBe(3);
    expect(component.paginatedData.length).toBe(5);
  });

  it('should handle row selection', () => {
    component.config.selectable = true;
    component.config.multiSelect = true;
    component.ngOnInit();
    fixture.detectChanges();
    
    expect(component.selectedRows.length).toBe(0);
    
    component.toggleRowSelection(mockData[0]);
    expect(component.selectedRows.length).toBe(1);
    expect(component.isRowSelected(mockData[0])).toBeTrue();
    
    component.toggleRowSelection(mockData[1]);
    expect(component.selectedRows.length).toBe(2);
    
    component.toggleRowSelection(mockData[0]);
    expect(component.selectedRows.length).toBe(1);
    expect(component.isRowSelected(mockData[0])).toBeFalse();
  });

  it('should handle single selection mode', () => {
    component.config.selectable = true;
    component.config.multiSelect = false;
    component.ngOnInit();
    fixture.detectChanges();
    
    component.toggleRowSelection(mockData[0]);
    expect(component.selectedRows.length).toBe(1);
    
    component.toggleRowSelection(mockData[1]);
    expect(component.selectedRows.length).toBe(1);
    expect(component.isRowSelected(mockData[0])).toBeFalse();
    expect(component.isRowSelected(mockData[1])).toBeTrue();
  });

  it('should handle select all functionality', () => {
    component.config.selectable = true;
    component.config.multiSelect = true;
    component.ngOnInit();
    fixture.detectChanges();
    
    expect(component.isAllSelected()).toBeFalse();
    expect(component.isSomeSelected()).toBeFalse();
    
    component.toggleAllSelection();
    expect(component.selectedRows.length).toBe(component.paginatedData.length);
    expect(component.isAllSelected()).toBeTrue();
    
    component.toggleAllSelection();
    expect(component.selectedRows.length).toBe(0);
    expect(component.isAllSelected()).toBeFalse();
  });

  it('should emit selection changes', () => {
    spyOn(component.selectionChange, 'emit');
    component.config.selectable = true;
    component.ngOnInit();
    
    component.toggleRowSelection(mockData[0]);
    expect(component.selectionChange.emit).toHaveBeenCalledWith([mockData[0]]);
  });

  it('should show loading state', () => {
    component.loading = true;
    fixture.detectChanges();
    
    const loadingElement = fixture.nativeElement.querySelector('.table-loading');
    expect(loadingElement).toBeTruthy();
    expect(loadingElement.textContent).toContain('Loading data...');
  });

  it('should show error state', () => {
    component.error = 'Failed to load data';
    fixture.detectChanges();
    
    const errorElement = fixture.nativeElement.querySelector('.table-error');
    expect(errorElement).toBeTruthy();
    expect(errorElement.textContent).toContain('Failed to load data');
  });

  it('should show empty state', () => {
    component.data = [];
    component.ngOnInit();
    fixture.detectChanges();
    
    const emptyElement = fixture.nativeElement.querySelector('.table-empty');
    expect(emptyElement).toBeTruthy();
    expect(emptyElement.textContent).toContain('No data available');
  });

  it('should handle action clicks', () => {
    component.ngOnInit();
    fixture.detectChanges();
    
    const editAction = component.actions[0];
    editAction.action(mockData[0]);
    
    expect(editAction.action).toHaveBeenCalledWith(mockData[0]);
  });

  it('should filter visible actions', () => {
    const actionWithVisibility: DataTableAction = {
      label: 'Special',
      action: jasmine.createSpy(),
      visible: (row) => row.status === 'active'
    };
    
    component.actions = [...mockActions, actionWithVisibility];
    
    const visibleForActive = component.getVisibleActions(mockData[0]);
    const visibleForInactive = component.getVisibleActions(mockData[1]);
    
    expect(visibleForActive.length).toBe(3);
    expect(visibleForInactive.length).toBe(2);
  });

  it('should handle disabled actions', () => {
    component.ngOnInit();
    fixture.detectChanges();
    
    const deleteAction = component.actions[1];
    expect(deleteAction.disabled!(mockData[1])).toBeTrue();
    expect(deleteAction.disabled!(mockData[0])).toBeFalse();
  });

  it('should get cell values correctly', () => {
    const nestedData = { user: { profile: { name: 'John Doe' } } };
    const nestedColumn: DataTableColumn = { key: 'user.profile.name', label: 'Name' };
    
    const value = component.getCellValue(nestedData, nestedColumn);
    expect(value).toBe('John Doe');
  });

  it('should handle column filters', () => {
    component.config.showColumnFilters = true;
    component.ngOnInit();
    fixture.detectChanges();
    
    component.columnFilters['status'] = 'active';
    component.onColumnFilter();
    
    expect(component.filteredData.length).toBe(2);
    expect(component.filteredData.every(item => item.status === 'active')).toBeTrue();
  });

  it('should get unique values for column filters', () => {
    component.ngOnInit();
    
    const statusValues = component.getUniqueValues('status');
    expect(statusValues).toEqual(['active', 'inactive']);
  });

  it('should emit events correctly', () => {
    spyOn(component.sortChange, 'emit');
    spyOn(component.pageChange, 'emit');
    spyOn(component.searchChange, 'emit');
    
    component.ngOnInit();
    
    component.onSort('name');
    expect(component.sortChange.emit).toHaveBeenCalledWith({ column: 'name', direction: 'asc' });
    
    component.goToPage(2);
    expect(component.pageChange.emit).toHaveBeenCalledWith(2);
    
    component.searchTerm = 'test';
    component.onSearch();
    expect(component.searchChange.emit).toHaveBeenCalledWith('test');
  });

  it('should clear selection', () => {
    component.config.selectable = true;
    component.selectedRows = [mockData[0], mockData[1]];
    
    spyOn(component.selectionChange, 'emit');
    
    component.clearSelection();
    
    expect(component.selectedRows.length).toBe(0);
    expect(component.selectionChange.emit).toHaveBeenCalledWith([]);
  });

  it('should track by function work correctly', () => {
    component.trackByProperty = 'id';
    
    const result = component.trackByFn(0, mockData[0]);
    expect(result).toBe(1);
    
    component.trackByProperty = undefined;
    const indexResult = component.trackByFn(0, mockData[0]);
    expect(indexResult).toBe(0);
  });
});