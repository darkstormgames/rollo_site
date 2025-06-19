import { Component, Input, Output, EventEmitter, OnInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';

export interface DataTableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  searchable?: boolean;
  type?: 'text' | 'number' | 'date' | 'boolean' | 'custom';
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, row: any) => string;
}

export interface DataTableAction {
  label: string;
  icon?: string;
  action: (row: any) => void;
  disabled?: (row: any) => boolean;
  visible?: (row: any) => boolean;
  class?: string;
  tooltip?: string;
}

export interface DataTableConfig {
  pageSize?: number;
  showPagination?: boolean;
  showSearch?: boolean;
  showColumnFilters?: boolean;
  selectable?: boolean;
  multiSelect?: boolean;
  striped?: boolean;
  bordered?: boolean;
  hover?: boolean;
  responsive?: boolean;
}

@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule, FormsModule, LoadingSpinnerComponent],
  template: `
    <div class="data-table-container" [class.responsive]="config.responsive">
      <!-- Search and Filters -->
      <div class="table-controls" *ngIf="config.showSearch || config.showColumnFilters">
        <div class="search-controls" *ngIf="config.showSearch">
          <input
            type="text"
            class="search-input"
            [(ngModel)]="searchTerm"
            (input)="onSearch()"
            placeholder="Search..."
            aria-label="Search table data">
          <span class="search-icon" aria-hidden="true">🔍</span>
        </div>
        
        <div class="column-filters" *ngIf="config.showColumnFilters">
          <select
            *ngFor="let column of searchableColumns"
            class="column-filter"
            [(ngModel)]="columnFilters[column.key]"
            (change)="onColumnFilter()"
            [attr.aria-label]="'Filter by ' + column.label">
            <option value="">All {{ column.label }}</option>
            <option *ngFor="let value of getUniqueValues(column.key)" [value]="value">
              {{ value }}
            </option>
          </select>
        </div>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="table-loading">
        <app-loading-spinner size="medium"></app-loading-spinner>
        <p>Loading data...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error && !loading" class="table-error" role="alert">
        <p>{{ error }}</p>
        <button *ngIf="onRetry" class="btn btn-primary" (click)="onRetry.emit()">
          Try Again
        </button>
      </div>

      <!-- Empty State -->
      <div *ngIf="!loading && !error && filteredData.length === 0" class="table-empty">
        <p>{{ emptyMessage || 'No data available' }}</p>
      </div>

      <!-- Data Table -->
      <div *ngIf="!loading && !error && filteredData.length > 0" class="table-wrapper">
        <table 
          class="data-table"
          [class.striped]="config.striped"
          [class.bordered]="config.bordered"
          [class.hover]="config.hover"
          role="table"
          [attr.aria-label]="tableAriaLabel">
          
          <!-- Table Header -->
          <thead>
            <tr role="row">
              <th *ngIf="config.selectable" class="select-column" role="columnheader">
                <input
                  *ngIf="config.multiSelect"
                  type="checkbox"
                  [checked]="isAllSelected()"
                  [indeterminate]="isSomeSelected()"
                  (change)="toggleAllSelection()"
                  aria-label="Select all rows">
              </th>
              
              <th
                *ngFor="let column of columns"
                [style.width]="column.width"
                [style.text-align]="column.align || 'left'"
                [class.sortable]="column.sortable"
                (click)="column.sortable ? onSort(column.key) : null"
                [attr.aria-sort]="getSortDirection(column.key)"
                role="columnheader"
                tabindex="0"
                (keydown.enter)="column.sortable ? onSort(column.key) : null"
                (keydown.space)="column.sortable ? onSort(column.key) : null">
                
                <span class="column-header">
                  {{ column.label }}
                  <span *ngIf="column.sortable" class="sort-indicator" [attr.aria-hidden]="true">
                    <span [class.active]="sortColumn === column.key && sortDirection === 'asc'">↑</span>
                    <span [class.active]="sortColumn === column.key && sortDirection === 'desc'">↓</span>
                  </span>
                </span>
              </th>
              
              <th *ngIf="actions.length > 0" class="actions-column" role="columnheader">
                Actions
              </th>
            </tr>
          </thead>
          
          <!-- Table Body -->
          <tbody>
            <tr
              *ngFor="let row of paginatedData; trackBy: trackByFn; let i = index"
              [class.selected]="isRowSelected(row)"
              [attr.aria-rowindex]="i + 1"
              role="row">
              
              <td *ngIf="config.selectable" class="select-cell" role="gridcell">
                <input
                  type="checkbox"
                  [checked]="isRowSelected(row)"
                  (change)="toggleRowSelection(row)"
                  [attr.aria-label]="'Select row ' + (i + 1)">
              </td>
              
              <td
                *ngFor="let column of columns"
                [style.text-align]="column.align || 'left'"
                role="gridcell"
                [attr.data-label]="column.label">
                
                <span *ngIf="!column.render">
                  {{ getCellValue(row, column) }}
                </span>
                
                <span *ngIf="column.render" [innerHTML]="column.render(getCellValue(row, column), row)">
                </span>
              </td>
              
              <td *ngIf="actions.length > 0" class="actions-cell" role="gridcell">
                <div class="action-buttons">
                  <button
                    *ngFor="let action of getVisibleActions(row)"
                    class="action-btn"
                    [class]="action.class || 'btn-secondary'"
                    [disabled]="action.disabled ? action.disabled(row) : false"
                    [title]="action.tooltip || action.label"
                    [attr.aria-label]="action.label"
                    (click)="action.action(row)">
                    <span *ngIf="action.icon" [attr.aria-hidden]="true">{{ action.icon }}</span>
                    <span class="action-label">{{ action.label }}</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div *ngIf="config.showPagination && filteredData.length > config.pageSize!" class="pagination-container">
        <div class="pagination-info">
          Showing {{ getStartIndex() + 1 }} to {{ getEndIndex() }} of {{ filteredData.length }} entries
        </div>
        
        <nav class="pagination" role="navigation" aria-label="Table pagination">
          <button
            class="page-btn"
            [disabled]="currentPage === 1"
            (click)="goToPage(1)"
            aria-label="Go to first page">
            ⟪
          </button>
          
          <button
            class="page-btn"
            [disabled]="currentPage === 1"
            (click)="goToPage(currentPage - 1)"
            aria-label="Go to previous page">
            ⟨
          </button>
          
          <span class="page-info">
            Page {{ currentPage }} of {{ getTotalPages() }}
          </span>
          
          <button
            class="page-btn"
            [disabled]="currentPage === getTotalPages()"
            (click)="goToPage(currentPage + 1)"
            aria-label="Go to next page">
            ⟩
          </button>
          
          <button
            class="page-btn"
            [disabled]="currentPage === getTotalPages()"
            (click)="goToPage(getTotalPages())"
            aria-label="Go to last page">
            ⟫
          </button>
        </nav>
      </div>

      <!-- Selection Info -->
      <div *ngIf="config.selectable && selectedRows.length > 0" class="selection-info" role="status">
        {{ selectedRows.length }} row(s) selected
        <button class="btn btn-secondary btn-sm" (click)="clearSelection()">
          Clear Selection
        </button>
      </div>
    </div>
  `,
  styleUrls: ['./data-table.component.css']
})
export class DataTableComponent implements OnInit, OnChanges {
  @Input() data: any[] = [];
  @Input() columns: DataTableColumn[] = [];
  @Input() actions: DataTableAction[] = [];
  @Input() config: DataTableConfig = {};
  @Input() loading = false;
  @Input() error: string | null = null;
  @Input() emptyMessage?: string;
  @Input() tableAriaLabel?: string;
  @Input() trackByProperty?: string;
  
  @Output() selectionChange = new EventEmitter<any[]>();
  @Output() sortChange = new EventEmitter<{column: string, direction: 'asc' | 'desc'}>();
  @Output() pageChange = new EventEmitter<number>();
  @Output() searchChange = new EventEmitter<string>();
  @Output() onRetry = new EventEmitter<void>();

  // Internal state
  filteredData: any[] = [];
  paginatedData: any[] = [];
  selectedRows: any[] = [];
  searchTerm = '';
  columnFilters: {[key: string]: string} = {};
  sortColumn = '';
  sortDirection: 'asc' | 'desc' = 'asc';
  currentPage = 1;

  // Computed properties
  searchableColumns: DataTableColumn[] = [];

  ngOnInit() {
    this.initializeConfig();
    this.initializeColumns();
    this.updateData();
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['data'] || changes['columns']) {
      this.updateData();
    }
  }

  private initializeConfig() {
    this.config = {
      pageSize: 10,
      showPagination: true,
      showSearch: true,
      showColumnFilters: false,
      selectable: false,
      multiSelect: false,
      striped: true,
      bordered: false,
      hover: true,
      responsive: true,
      ...this.config
    };
  }

  private initializeColumns() {
    this.searchableColumns = this.columns.filter(col => col.searchable);
  }

  private updateData() {
    this.filteredData = this.getFilteredData();
    this.updatePagination();
  }

  private getFilteredData(): any[] {
    let filtered = [...this.data];

    // Apply search filter
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(row =>
        this.columns.some(col =>
          col.searchable && 
          this.getCellValue(row, col)?.toString().toLowerCase().includes(term)
        )
      );
    }

    // Apply column filters
    Object.keys(this.columnFilters).forEach(key => {
      const filterValue = this.columnFilters[key];
      if (filterValue) {
        filtered = filtered.filter(row =>
          this.getCellValue(row, { key } as DataTableColumn)?.toString() === filterValue
        );
      }
    });

    // Apply sorting
    if (this.sortColumn) {
      filtered.sort((a, b) => {
        const aVal = this.getCellValue(a, { key: this.sortColumn } as DataTableColumn);
        const bVal = this.getCellValue(b, { key: this.sortColumn } as DataTableColumn);
        
        let result = 0;
        if (aVal < bVal) result = -1;
        else if (aVal > bVal) result = 1;
        
        return this.sortDirection === 'desc' ? -result : result;
      });
    }

    return filtered;
  }

  private updatePagination() {
    if (!this.config.showPagination) {
      this.paginatedData = this.filteredData;
      return;
    }

    const startIndex = (this.currentPage - 1) * this.config.pageSize!;
    const endIndex = startIndex + this.config.pageSize!;
    this.paginatedData = this.filteredData.slice(startIndex, endIndex);
  }

  getCellValue(row: any, column: DataTableColumn): any {
    return this.getNestedProperty(row, column.key);
  }

  private getNestedProperty(obj: any, path: string): any {
    return path.split('.').reduce((o, p) => o?.[p], obj);
  }

  onSearch() {
    this.currentPage = 1;
    this.updateData();
    this.searchChange.emit(this.searchTerm);
  }

  onColumnFilter() {
    this.currentPage = 1;
    this.updateData();
  }

  onSort(columnKey: string) {
    if (this.sortColumn === columnKey) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = columnKey;
      this.sortDirection = 'asc';
    }
    
    this.updateData();
    this.sortChange.emit({ column: this.sortColumn, direction: this.sortDirection });
  }

  getSortDirection(columnKey: string): string | null {
    if (this.sortColumn !== columnKey) return null;
    return this.sortDirection;
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.getTotalPages()) {
      this.currentPage = page;
      this.updatePagination();
      this.pageChange.emit(this.currentPage);
    }
  }

  getTotalPages(): number {
    return Math.ceil(this.filteredData.length / this.config.pageSize!);
  }

  getStartIndex(): number {
    return (this.currentPage - 1) * this.config.pageSize!;
  }

  getEndIndex(): number {
    return Math.min(this.getStartIndex() + this.config.pageSize!, this.filteredData.length);
  }

  // Selection methods
  isRowSelected(row: any): boolean {
    return this.selectedRows.includes(row);
  }

  toggleRowSelection(row: any) {
    if (this.config.multiSelect) {
      const index = this.selectedRows.indexOf(row);
      if (index > -1) {
        this.selectedRows.splice(index, 1);
      } else {
        this.selectedRows.push(row);
      }
    } else {
      this.selectedRows = this.isRowSelected(row) ? [] : [row];
    }
    
    this.selectionChange.emit([...this.selectedRows]);
  }

  isAllSelected(): boolean {
    return this.paginatedData.length > 0 && 
           this.paginatedData.every(row => this.isRowSelected(row));
  }

  isSomeSelected(): boolean {
    return this.selectedRows.length > 0 && !this.isAllSelected();
  }

  toggleAllSelection() {
    if (this.isAllSelected()) {
      this.selectedRows = this.selectedRows.filter(row => !this.paginatedData.includes(row));
    } else {
      this.paginatedData.forEach(row => {
        if (!this.isRowSelected(row)) {
          this.selectedRows.push(row);
        }
      });
    }
    
    this.selectionChange.emit([...this.selectedRows]);
  }

  clearSelection() {
    this.selectedRows = [];
    this.selectionChange.emit([]);
  }

  getVisibleActions(row: any): DataTableAction[] {
    return this.actions.filter(action => 
      !action.visible || action.visible(row)
    );
  }

  getUniqueValues(columnKey: string): string[] {
    const values = this.data
      .map(row => this.getCellValue(row, { key: columnKey } as DataTableColumn))
      .filter(value => value != null && value !== '')
      .map(value => value.toString());
    
    return [...new Set(values)].sort();
  }

  trackByFn = (index: number, item: any): any => {
    return this.trackByProperty ? item[this.trackByProperty] : index;
  };
}