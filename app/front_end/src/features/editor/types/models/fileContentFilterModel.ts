import { FilterEnum } from "../enums/filterEnum";

export interface FileContentFilterModel {
  [column: string]: {operator: FilterEnum, value: string};
}