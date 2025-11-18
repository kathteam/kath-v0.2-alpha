import { FileTypes } from './models/fileModel';

export type FileTreeViewItemProps = {
  fileType?: FileTypes;
  id: string;
  label: string;
};
