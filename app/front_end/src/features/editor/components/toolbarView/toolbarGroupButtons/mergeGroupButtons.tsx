import { ToolbarGroupItem, ToolbarGroupItemProps } from '@/features/editor/components/toolbarView';
import { useToolbarContext, useWorkspaceContext } from '@/features/editor/hooks';
import { defaultSaveTo } from '@/features/editor/stores';
import { findUniqueFileName, generateTimestamp, getFileExtension } from '@/features/editor/utils';
import { useStatusContext } from '@/hooks';
import { axios } from '@/lib';
import { Endpoints } from '@/types';
import { MergeType as MergeTypeIcon } from '@mui/icons-material';
import { useCallback, useMemo } from 'react';

export interface MergeGroupButtonsProps {}

export const MergeGroupButtons: React.FC<MergeGroupButtonsProps> = () => {
  const { blockedStateUpdate } = useStatusContext();
  const { fileTree, openFileByPath } = useWorkspaceContext();
  const {
    saveTo,
    saveToErrorStateUpdate,
    override,
    lovdFile,
    clinvarFile,
    gnomadFile,
    customFile,
    lovdErrorStateUpdate,
    clinvarErrorStateUpdate,
    gnomadErrorStateUpdate,
    openAfterSave,
  } = useToolbarContext();

  const mergeAllClick = useCallback(async () => {
    lovdErrorStateUpdate('');
    clinvarErrorStateUpdate('');
    gnomadErrorStateUpdate('');

    if (!lovdFile) lovdErrorStateUpdate('Please select a LOVD file');
    if (!clinvarFile) clinvarErrorStateUpdate('Please select a ClinVar file');
    if (!gnomadFile) gnomadErrorStateUpdate('Please select a gnomAD file');
    if (!lovdFile || !clinvarFile || !gnomadFile) return;

    blockedStateUpdate(true);

    try {
      const timestamp = generateTimestamp();
      const savePath =
        saveTo !== defaultSaveTo ? saveTo.id : findUniqueFileName(fileTree, `all_merged_${timestamp}.csv`);
      if (getFileExtension(savePath) !== 'csv') {
        saveToErrorStateUpdate('Select .csv');
        return;
      }

      await axios.get(`${Endpoints.WORKSPACE_MERGE}/all/${savePath}`, {
        params: {
          override,
          lovdFile: lovdFile.id,
          clinvarFile: clinvarFile.id,
          gnomadFile: gnomadFile.id,
          customFile: customFile?.id || '',
        },
      });
      // Open file after saving
      if (openAfterSave) openFileByPath(savePath);
      // ---
    } catch (error) {
      console.error('Error merging all files:', error);
    } finally {
      blockedStateUpdate(false);
    }
  }, [saveTo, override, lovdFile, gnomadFile, clinvarFile, customFile, openAfterSave]);

  const mergeLovdAndGnomadClick = useCallback(async () => {
    clinvarErrorStateUpdate('');

    if (!lovdFile) lovdErrorStateUpdate('Please select a LOVD file');
    if (!gnomadFile) gnomadErrorStateUpdate('Please select a gnomAD file');
    if (!lovdFile || !gnomadFile) return;

    blockedStateUpdate(true);

    try {
      const timestamp = generateTimestamp();
      const savePath =
        saveTo !== defaultSaveTo ? saveTo.id : findUniqueFileName(fileTree, `lovd_gnomad_${timestamp}.csv`);
      if (getFileExtension(savePath) !== 'csv') {
        saveToErrorStateUpdate('Select .csv');
        return;
      }

      await axios.get(`${Endpoints.WORKSPACE_MERGE}/lovd_gnomad/${savePath}`, {
        params: {
          override,
          lovdFile: lovdFile.id,
          gnomadFile: gnomadFile.id,
        },
      });
      // Open file after saving
      if (openAfterSave) openFileByPath(savePath);
      // ---
    } catch (error) {
      console.error('Error merging LOVD & gnomAD files:', error);
    } finally {
      blockedStateUpdate(false);
    }
  }, [saveTo, override, lovdFile, gnomadFile, openAfterSave]);

  const mergeLovdAndClinvarClick = useCallback(async () => {
    gnomadErrorStateUpdate('');

    if (!lovdFile) lovdErrorStateUpdate('Please select a LOVD file');
    if (!clinvarFile) clinvarErrorStateUpdate('Please select a ClinVar file');
    if (!lovdFile || !clinvarFile) return;

    blockedStateUpdate(true);

    try {
      const timestamp = generateTimestamp();
      const savePath =
        saveTo !== defaultSaveTo ? saveTo.id : findUniqueFileName(fileTree, `lovd_clinvar_${timestamp}.csv`);
      if (getFileExtension(savePath) !== 'csv') {
        saveToErrorStateUpdate('Select .csv');
        return;
      }

      await axios.get(`${Endpoints.WORKSPACE_MERGE}/lovd_clinvar/${savePath}`, {
        params: {
          override,
          lovdFile: lovdFile.id,
          clinvarFile: clinvarFile.id,
        },
      });
      // Open file after saving
      if (openAfterSave) openFileByPath(savePath);
      // ---
    } catch (error) {
      console.error('Error merging LOVD & ClinVar files:', error);
    } finally {
      blockedStateUpdate(false);
    }
  }, [saveTo, override, lovdFile, clinvarFile, openAfterSave]);

  const buttons: ToolbarGroupItemProps[] = useMemo(
    () => [
      {
        group: 'merge',
        icon: MergeTypeIcon,
        label: 'Merge All',
        onClick: mergeAllClick,
      },
      {
        group: 'merge',
        icon: MergeTypeIcon,
        label: 'Merge LOVD & gnomAD',
        onClick: mergeLovdAndGnomadClick,
      },
      {
        group: 'merge',
        icon: MergeTypeIcon,
        label: 'Merge LOVD & ClinVar',
        onClick: mergeLovdAndClinvarClick,
      },
    ],
    [mergeLovdAndGnomadClick, mergeLovdAndClinvarClick, mergeAllClick]
  );

  return (
    <>
      {buttons.map((button, index) => (
        <ToolbarGroupItem key={index} {...button} />
      ))}
    </>
  );
};
