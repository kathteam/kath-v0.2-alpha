import pandas as pd
import sqlite3

from tqdm import tqdm

from src.utils.logger import Logger

logger = Logger.get(__name__)        

def assign_revel_scores(input_gene_data: pd.DataFrame, revel_db_file: str) -> pd.DataFrame:
    """
    Assigns REVEL scores with progress tracking and optimized processing.
    
    Args:
        input_gene_data: DataFrame with hg38_gnomad_format column
        revel_db_file: Path to REVEL SQLite database
        
    Returns:
        DataFrame with added REVEL scores
    """
    total_rows = input_gene_data.shape[0]
    logger.info(f"Starting REVEL score assignment for {total_rows} variants")
    with tqdm(total = total_rows, desc = "Assigning REVEL scores", unit = "Rows", unit_scale = True) as pbar:
        for i in range(total_rows):
            pbar.update(1)
            hg38_gnomad_format = input_gene_data.loc[i, 'hg38_gnomad_format']
                
            if pd.isna(hg38_gnomad_format):
                hg38_gnomad_format = input_gene_data.loc[i, 'variant_id_gnomad']
                
            try:
                chromosome, position, ref, alt = hg38_gnomad_format.split('-')
                revel_score = get_single_revel_score(chromosome, position, ref, alt, revel_db_file)
                input_gene_data.loc[i, 'REVEL'] = revel_score
                
            except ValueError as ve:
                input_gene_data.loc[i, 'REVEL'] = pd.NA
                logger.error(f"Format error in variant {hg38_gnomad_format}: {ve}")
                
            except Exception as e:
                input_gene_data.loc[i, 'REVEL'] = pd.NA
                logger.error(f"Failed to get REVEL score for {hg38_gnomad_format}: {e}")
    
    logger.info("REVEL score assignment complete")
    return input_gene_data
    

def get_single_revel_score(chromosome, grch38_position, ref, alt, revel_db_file):


    conn = sqlite3.connect(revel_db_file)
    cursor = conn.cursor()
    
    query = '''
    SELECT chr, grch38_pos, ref, alt, REVEL
    FROM revel
    WHERE chr = ? AND grch38_pos = ? AND ref = ? AND alt = ?
    '''
    
    params = [chromosome, grch38_position, ref, alt]
    
    cursor.execute(query, params)
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[4]
    else:
        return pd.NA
    

def main_revel_pipeline(dataset_path: str, revel_db_path: str) -> pd.DataFrame:
    
    # Read the input gene data
    try:
        input_gene_data = pd.read_csv(dataset_path)
        
        # Assign REVEL scores
        print("Assigning REVEL scores... \n Errors will be logged.")
        input_gene_data = assign_revel_scores(input_gene_data, revel_db_path)
        
        return input_gene_data
        
    except FileNotFoundError:
        print(f"File not found: {dataset_path}")
        raise
    
    except pd.errors.EmptyDataError:
        print(f"Empty file: {dataset_path}")
        raise

if __name__ == '__main__':
    main_revel_pipeline()
    
