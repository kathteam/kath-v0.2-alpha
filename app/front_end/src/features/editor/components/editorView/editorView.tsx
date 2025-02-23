import {
  EditorColumnMenu,
  EditorConfirmLeave,
  EditorHeader,
  EditorToolbar,
} from '@/features/editor/components/editorView';
import { useWorkspaceContext } from '@/features/editor/hooks';
import {
  FileContentAggregationActions,
  FileDataRequestDTO,
  FileDataResponseDTO,
  FilterEnum,
  SortEnum,
} from '@/features/editor/types';
import { useSessionContext, useStatusContext } from '@/hooks';
import { axios } from '@/lib';
import { Endpoints } from '@/types';
import { DataGrid, GridPagination, useGridApiRef } from '@mui/x-data-grid';
import { useCallback, useEffect, useState } from 'react';

/**
 * `EditorView` component is a data grid view that allows users to interact with and manipulate file content within the editor.
 *
 * @description
 * The `EditorView` component:
 * - Displays a data grid with file content, including rows and columns.
 * - Allows users to edit the file content and save changes.
 * - Supports pagination and data aggregation functionalities.
 * - Utilizes the `DataGrid` component from Material-UI's X Data Grid library to render and manage the grid.
 *
 * The component integrates with:
 * - `WorkspaceContext` to manage the file state, content, and pagination.
 * - `SessionContext` to handle connection status.
 * - Axios for making API requests to fetch and save file content.
 * - WebSocket for real-time updates.
 *
 * Key functionalities include:
 * - Fetching file content from the backend and updating the grid when the file or pagination changes.
 * - Handling pagination changes and updating the file state accordingly.
 * - Supporting data aggregation actions like sum, average, etc., which can be triggered via the column menu.
 * - Saving changes to the file content and updating the server with new data and aggregations.
 *
 * @component
 *
 * @example
 * // Usage of the EditorView component within a parent component
 * import React from 'react';
 * import { EditorView } from '@/features/editor/components/editorView';
 *
 * const MyEditorPage = () => (
 *   <div style={{ height: '600px', width: '100%' }}>
 *     <EditorView />
 *   </div>
 * );
 *
 * export default MyEditorPage;
 *
 * @returns {JSX.Element} The rendered data grid view component.
 */
export const EditorView: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [fileContentResponse, setFileContentResponse] = useState<FileDataResponseDTO>({
    totalRows: 0,
    header: [],
    rows: [],
    page: 0,
  });

  const { connected } = useSessionContext();
  const { file, fileContent, filePagination, fileStateUpdate } = useWorkspaceContext();
  const { blocked, blockedStateUpdate, unsaved, unsavedStateUpdate } = useStatusContext();
  const ref = useGridApiRef();

  const handleSave = async () => {
    blockedStateUpdate(true);

    const data: FileDataRequestDTO = {
      page: filePagination.page,
      rowsPerPage: filePagination.rowsPerPage,
      header: ref.current.getAllColumns().map((column) => column.field),
      rows: ref.current
        .getAllRowIds()
        .map((rowId) => ref.current.getAllColumns().map((column) => ref.current.getCellValue(rowId, column.field))),
    };

    try {
      await axios.put<FileDataResponseDTO>(`${Endpoints.WORKSPACE_FILE}/${file.id}`, data, {
        params: {
          sorts: JSON.stringify(fileContent.sorts),
          filters: JSON.stringify(fileContent.filters),
        },
      });

      await getWorkspaceFile();

      const responseAggregate = await axios.get(`${Endpoints.WORKSPACE_AGGREGATE}/all/${file.id}`, {
        params: {
          columnsAggregation: JSON.stringify(fileContent.aggregations),
        },
      });

      const { columnsAggregation: responseColumnsAggregation } = responseAggregate.data;
      fileStateUpdate(undefined, { ...fileContent, aggregations: responseColumnsAggregation }, undefined);
    } catch (error) {
      console.error('Failed to save file content:', error);
    } finally {
      blockedStateUpdate(false);
    }
  };

  const handleAggregation = async (column: string, action: FileContentAggregationActions) => {
    switch (action) {
      case FileContentAggregationActions.NONE:
        const { [column]: _, ...rest } = fileContent.aggregations;
        fileStateUpdate(undefined, { ...fileContent, aggregations: rest }, undefined);
        break;
      default:
        {
          blockedStateUpdate(true);
          try {
            const response = await axios.get(`${Endpoints.WORKSPACE_AGGREGATE}/${file.id}`, {
              params: {
                field: column,
                action: action,
              },
            });

            const { field: responseField, action: responseAction, value: responseValue } = response.data;

            const newAggregations = {
              ...fileContent.aggregations,
              [responseField]: { action: responseAction, value: responseValue },
            };
            fileStateUpdate(undefined, { ...fileContent, aggregations: newAggregations }, undefined);
          } catch (error) {
            console.error('Failed to fetch aggregation data:', error);
          } finally {
            blockedStateUpdate(false);
          }
        }
        break;
    }
  };

  const handleSort = async (column: string, sort: SortEnum) => {
    if (sort === SortEnum.NONE) {
      console.log('Unsort column:', column);
      fileStateUpdate(undefined, { ...fileContent, sorts: {} }, undefined);
      return;
    }

    fileStateUpdate(undefined, { ...fileContent, sorts: { [column]: sort } }, undefined);
  };

  const handleFilter = async (column: string, operator: FilterEnum, value: string) => {
    fileStateUpdate(undefined, { ...fileContent, filters: { [column]: { operator, value } } }, undefined);
  }

  const handleFilterClear = async () => {
    fileStateUpdate(undefined, { ...fileContent, filters: {} }, undefined);
  }
  
  const onCellEditStart = () => {
    unsavedStateUpdate(true);
  };

  const getWorkspaceFile = useCallback(async () => {
    if (!file.id) {
      setFileContentResponse({ totalRows: 0, header: [], rows: [], page: 0 });
      return;
    }

    blockedStateUpdate(true);

    try {
      const response = await axios.get<FileDataResponseDTO>(`${Endpoints.WORKSPACE_FILE}/${file.id}`, {
        params: {
          page: filePagination.page,
          rowsPerPage: filePagination.rowsPerPage,
          sorts: JSON.stringify(fileContent.sorts),
          filters: JSON.stringify(fileContent.filters),
        },
      });

      setFileContentResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch file content:', error);
    } finally {
      setIsLoading(false);
      blockedStateUpdate(false);
    }
  }, [filePagination.page, filePagination.rowsPerPage, fileContent.sorts, fileContent.filters]);

  // File content fetching effect
  useEffect(() => {
    if (connected) getWorkspaceFile();
  }, [connected, getWorkspaceFile]);

  // Aggregation reset effect
  useEffect(() => {
    fileStateUpdate(
      undefined,
      { columns: fileContent.columns, rows: fileContent.rows, aggregations: {}, sorts: {}, filters: {}}, // TODO might need change on sorts and filters
      undefined
    );
  }, [file.id]);

  // Parse file content response effect
  useEffect(() => {
    const { totalRows, header, rows } = fileContentResponse;

    if (!header) {
      fileStateUpdate(
        undefined,
        { columns: [], rows: [], aggregations: fileContent.aggregations, sorts: fileContent.sorts, filters: fileContent.filters },
        undefined
      );
      return;
    }

    const parsedColumns = header.map((value) => {
      return {
        field: value,
        headerName: value,
        flex: 1,
        minWidth: 150,
        editable: true,
        renderHeader: () => (
          <EditorHeader
            columnName={value}
            gridColumnsAggregation={fileContent.aggregations}
            gridColumnsSort={fileContent.sorts}
            gridColumnsFilter={fileContent.filters}
          />
        ),
      };
    });

    const parsedRows = rows.map((row, index) => {
      return {
        "internal_datagrid_id": index,
        ...row.reduce((acc, value, index) => {
          return { ...acc, [header[index]]: value };
        }, {}),
      };
    });

    fileStateUpdate(
      undefined,
      { columns: parsedColumns, rows: parsedRows, aggregations: fileContent.aggregations, sorts: fileContent.sorts, filters: fileContent.filters },
      { page: filePagination.page, rowsPerPage: filePagination.rowsPerPage, totalRows: totalRows }
    );
  }, [fileContentResponse, fileContent.aggregations, fileContent.sorts, fileContent.filters]);

  // Browser tab close/refresh warning if there are unsaved changes effect
  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (unsaved) event.preventDefault();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [unsaved]);

  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [pendingModel, setPendingModel] = useState<{ page: number; pageSize: number } | null>(null);

  const [paginationModel, setPaginationModel] = useState({
    page: filePagination.page,
    pageSize: filePagination.rowsPerPage,
  });

  const handleConfirm = () => {
    if (pendingModel) {
      fileStateUpdate(undefined, undefined, {
        page: pendingModel.page,
        rowsPerPage: pendingModel.pageSize,
        totalRows: filePagination.totalRows,
      });
      setPaginationModel(pendingModel);
      setPendingModel(null);
    }
    setIsConfirmDialogOpen(false);
  };

  const handleCancel = () => {
    setPendingModel(null);
    setIsConfirmDialogOpen(false);
  };

  return (
    <>
      <DataGrid
        sx={{ height: '100%', border: 'none' }}
        loading={blocked || isLoading}
        rows={fileContent.rows}
        columns={fileContent.columns}
        getRowId={(row) => row.internal_datagrid_id}
        pagination
        paginationMode='server'
        rowCount={filePagination.totalRows}
        disableColumnSorting
        pageSizeOptions={[25, 50, 100]}
        paginationModel={paginationModel}
        onPaginationModelChange={(model) => {
          if (unsaved) {
            setPendingModel(model);
            setIsConfirmDialogOpen(true);
          } else {
            fileStateUpdate(undefined, undefined, {
              page: model.page,
              rowsPerPage: model.pageSize,
              totalRows: filePagination.totalRows,
            });
            setPaginationModel(model);
          }
        }}
        slots={{
          toolbar: (props) => <EditorToolbar {...props} handleSave={handleSave} />,
          columnMenu: (props) => (
            <EditorColumnMenu
              {...props}
              disabled={blocked}
              handleAggregation={handleAggregation}
              handleSort={handleSort}
              handleFilter={handleFilter}
              handleFilterClear={handleFilterClear}
            />
          ),
          pagination: (props) => <GridPagination disabled={blocked} {...props} />,
        }}
        slotProps={{
          toolbar: {},
        }}
        apiRef={ref}
        onCellEditStart={onCellEditStart}
      />
      <EditorConfirmLeave isOpen={isConfirmDialogOpen} onClose={handleCancel} onConfirm={handleConfirm} />
    </>
  );
};
