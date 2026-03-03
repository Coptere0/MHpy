import numpy as np
import pandas as pd
import os
from typing import Optional
from data_handling import natural_key
from swmm_api import read_rpt_file


#### Lecture des fichiers asc
def read_asc_file(file_path:str, ignore_first_line=True, metadata_len: int=6, encoding: str="utf-8"):
    """Reading of .asc files and extract its metadata and dat grid

    Args:
        file_path (str): file_path of the .asc file.
        ignore_first_line (bool, optional): If the first line of the file is not usefull. Defaults to True.
        metadata_len (int): Number of metadat line. Defaults to 6.
        encoding (str): Type of encoding. Defaults "utf-8"

    Returns:
        Tuple(dict[str, float], np.ndarray):
        Dictionary of metadata (e.g., ncols, nrows, xllcorner, yllcorner, cellsize, NODATA_value).
        2D numpy array of the grid data, with NaN for missing values.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or metadata is missing.

    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    with open(file_path, 'r', encoding=encoding) as f:
        # Si with title gnorer la première ligne (vide ou commentaire)
        if ignore_first_line: 
            f.readline()
         # Extraire les métadonnées
        metadata_lines = [f.readline().strip() for _ in range(6)]
        metadata = {}
        for line in metadata_lines:
            if not line:
                raise ValueError("Invalid metadata line in the .asc file.")
            try:
                key, value = line.split()
                metadata[key.strip()] = float(value.strip()) if '.' in value else int(value.strip())
            except ValueError:
                raise ValueError(f"Invalid metadata format: {line}")
        # Lire les données restantes avec genfromtxt
        data = np.genfromtxt(f, filling_values=-9999)  # Gère les valeurs manquantes
        data = data.astype(float)
        data = np.where(data==-9999,np.nan, data)
        return metadata, data
    

def read_general_input(file_path: str, encoding="utf-8") -> dict[str, str]:
    """Read the general input file

    Args:
        file_path (str): Path to the general input file
        encoding (str): Type of encoding. Default "utf-8"

    Returns:
        dict: informations about simulation (key: identifier, value: info)
    """
    with open(file_path, "r", encoding=encoding) as f:
        lines = [line.strip() for line in f if line.strip()]# Diviser en lignes
    general_input = {}
    for line in lines:
        key, value = line.split(maxsplit=1)  # Séparation en clé et valeur (1ère espace seulement)
        general_input[key.strip()] = value.strip()
    return general_input


#### Récupérer les chemins des fichiers inputs mentionnés dans général input ####
def get_inputoutput_files_path(file_path: str, encoding="utf-8") -> tuple[dict[str, str], dict[str, str]]:
    """ Extract input and output file paths from th surface configuration file.

    Args:
        file_path (str): Path to the surface configuration file
        encoding (str): Type of encoding. Default "utf-8"

    Returns:
        Tuple(Dict[str, str], Dict[str, str]):First dict: Input file paths (key: identifier, value: path). <br>Second dict: Output file paths (key: identifier, value: path).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, "r", encoding=encoding) as f:
        surface_file = [line.strip() for line in f.readlines()]# Diviser en lignes
    input_paths = [line for line in surface_file if "Inputs" in line]
    input_paths = {key.strip(): value.strip() for key,value in [line.split(' ', maxsplit=1) for line in input_paths] }
    output_paths = [line for line in surface_file if "Outputs" in line]
    output_paths = {key.strip(): value.strip() for key,value in [line.split(' ', maxsplit=1) for line in output_paths] }
    return input_paths, output_paths


### Récupérer les informations sur les noeuds ###
def get_nodes_coord(file_path: str, encoding='utf-8') -> Optional[pd.DataFrame]:
    """Extract node coordinates from the drainage input file, specifically from the [COORDINATES] section.

    Args:
        file_path (str): Path to the drainage input file.
        encoding (str): Type of encoding. Default "utf-8"

    Returns:
        pd.DataFrame: A DataFrame with columns ['Node', 'X', 'Y'] containing the node coordinates.
                      Returns None if the file or section is not found.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or the [COORDINATES] section is missing,
                    or if any value cannot be converted to a number.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    with open(file_path, 'r', encoding=encoding) as file:
        nodes = []
        lire_nodes = False
        for line in file:
            if line.strip() == '[COORDINATES]':
                lire_nodes = True
                continue
            if lire_nodes and line.strip().startswith('['):
                break  # Arrêter à la prochaine section
            if lire_nodes and line.strip() and not line.startswith(';;'):
                nodes.append(line.strip())
    if not nodes:
        raise ValueError("No node coordinates found in the [COORDINATES] section.")
    # Convertion en DataFrame
    df_nodes = pd.DataFrame([node.split() for node in nodes],
                            columns=['Node', 'X', 'Y'])
    df_nodes = df_nodes.apply(pd.to_numeric)
    df_nodes["Node"] = df_nodes["Node"].astype(int)
    return df_nodes


#### Récupérer les informations sur les conduits ####
def get_conduits(file_path: str, encoding="utf-8") -> Optional[pd.DataFrame]:
    """Extract conduits infomrations from the drainage input file, specifically from the [CONDUITS] section.

    Args:
        file_path (str): Path to the drainage input file
        encoding (str, optional): Type of encoding. Defaults to "utf-8".

    Returns:
        Optional[pd.DataFrame]: DataFrame with columns: <br> ID, From_Node, To_Node *as int* <br>Length, Roughness, InOffset, OutOffset, InitFlow, MaxFlow *as float*
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the [CONDUITS] section is missing or data is invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    conduits = []
    with open(file_path, 'r', encoding=encoding) as file:
        lire_conduit = False
        for line in file:
            if line.strip() == '[CONDUITS]':
                lire_conduit = True
                continue
            if lire_conduit and line.strip().startswith('['):
                break  # Arrêter à la prochaine section
            if lire_conduit and line.strip() and not line.startswith(';;'):
                conduits.append(line.strip())
    if not conduits:
        raise ValueError("No conduit information found in the [CONDUITS] section.")
        # Convertion en DataFrame
    df_conduits = pd.DataFrame([conduit.split() for conduit in conduits],
                            columns=['ID', 'From_Node', 'To_Node', 'Length', 
                                    'Roughness', 'InOffset', 'OutOffset', 
                                    'InitFlow', 'MaxFlow'])
       # Conversion stricte des colonnes numériques
    numeric_cols = ['Length', 'Roughness', 'InOffset', 'OutOffset', 'InitFlow', 'MaxFlow']
    for col in numeric_cols:
        df_conduits[col] = pd.to_numeric(df_conduits[col])

    # Conversion des colonnes d'identifiants en entiers
    int_cols = ['ID', 'From_Node', 'To_Node']
    for col in int_cols:
        df_conduits[col] = pd.to_numeric(df_conduits[col]).astype(int)
    return df_conduits


#### Récupérer la série temporelle de préipitation
def get_rain_serie(file_path: str,encoding='utf-8') -> pd.DataFrame:
    """Extract the rain serie from the surface file, between the GAGE line and the SNOW line

    Args:
        file_path (str): Path to the surface file
        encoding (str, optional): File encoding. Defaults to 'utf-8'.

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the timeserie section is missing or data is invalid.

    Returns:
        pd.DataFrame: DataFrame with columns:
        "intensity_m/s", "time", "intensity_mm/h", "intensity_mm/min" (as float)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding=encoding) as file:
        rain=[]
        lire_pluie = False
        for line in file:
            if 'GAGE ' in line.strip():
                lire_pluie = True
                continue
            if lire_pluie and line.strip().startswith('SNOW'):
                break  # Arrêter à la prochaine section
            if lire_pluie and line.strip() and "GAGE" not in line.strip():
                rain.append(line.strip())
    if not rain:
        raise ValueError("No rain serie found bellow 'GAGE' line.")
    df_rain = pd.DataFrame([line.split('\t') for line in rain], columns=["intensity_m/s", "time"])
    df_rain = df_rain.apply(pd.to_numeric)
    df_rain["intensity_mm/m"] = df_rain["intensity_m/s"] * 10**3 *60
    df_rain["intensity_mm/h"] = df_rain["intensity_mm/min"] *60
    return df_rain


def create_dict_luse(file_path: str, encoding="utf-8") -> dict[int, dict[str, any]]:
    """Return a dict of soil types properties based on the surface input file

    Args:
        file_path (str): Path to the surface file
        encoding (str, optional): File encoding. Defaults to "utf-8".

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or required sections (NSOILS, NLANDS) are missing.

    Returns:
        dict([int, dict[str, any]]): A dictionary where keys are soil IDs and values are dictionaries
                                   containing soil parameters (conduction, cap_suction, moisture_def, 
                                   name, manning, intercept_depth).

    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, "r", encoding=encoding) as f:
        surface_file = [line.strip() for line in f if line.strip()]

    soils = []
    soil_param_by_id = {}

    # 1) Extract NSOILS and soil parameters
    try:
        nsoils_line = next(line for line in surface_file if line.startswith("NSOILS"))
        nsoils = int(nsoils_line.split()[1])
        start_index = surface_file.index(nsoils_line) + 1
    except (StopIteration, IndexError, ValueError) as e:
        raise ValueError("Invalid or missing NSOILS section in the file.") from e

    for idx in range(nsoils):
        try:
            raw = surface_file[start_index + idx]
            cond, cap_suct, moist_def, *name_parts = raw.split(maxsplit=3)
            name = " ".join(name_parts)  # Handle names with spaces
            soils.append({
                "id": idx + 1,
                "conduction": float(cond),
                "cap_suction": float(cap_suct),
                "moisture_def": float(moist_def),
                "name": name
            })
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid soil data format at line {start_index + idx}: {raw}") from e

    soil_param_by_id = {s["id"]: s for s in soils}

    # 2) Extract NLANDS and land parameters
    try:
        nlands_line = next(line for line in surface_file if line.startswith("NLANDS"))
        nland = int(nlands_line.split()[1])
        start_index = surface_file.index(nlands_line) + 1
    except (StopIteration, IndexError, ValueError) as e:
        raise ValueError("Invalid or missing NLANDS section in the file.") from e

    for idx in range(nland):
        try:
            raw = surface_file[start_index + idx]
            manning, intercept_depth, *name_parts = raw.split(maxsplit=2)
            soil_id = idx + 1
            if soil_id in soil_param_by_id:
                soil_param_by_id[soil_id].update({
                    "manning": float(manning),
                    "intercept_depth": float(intercept_depth)
                })
            else:
                raise ValueError(f"No matching soil ID found for land parameters at line {start_index + idx}: {raw}")
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid land data format at line {start_index + idx}: {raw}") from e

    return soil_param_by_id


def get_timed_grid(grid_files_paths: list[str], ignore_first_line: bool=False,
                   metadata_len=6, encoding: str="utf-8") -> tuple[dict, np.array]:
    """Reads and merges multiple ASC grid files into a single 3D NumPy array, along with their metadata.

    Args:
        grid_files_paths (list[str]): List of the path to the different files to read
        ignore_first_line (bool, optional): If the first line of the file is not usefull. Defaults to True.
        metadata_len (int): Number of metadat line. Defaults to 6.
        encoding (str): Type of encoding. Defaults "utf-8"

    Returns:
        tuple ([dict, np.array]): A tuple containing : <br> *dict* Metadata from the first ASC file, including spatial reference information. <br> *np.ndarray* A 3D NumPy array where each 2D slice corresponds to a grid from the input files.
        
    Notes: 
    - Only ASC files are processed; files with "xml" in their name are ignored.
    - The order of grids in `grids_merged` follows the order of files in `grid_files`.
    """
    grids = []
    for path in grid_files_paths:
        # Dont use xml files
        if "xml" not in path:
            metadata, data = read_asc_file(path, ignore_first_line=ignore_first_line,
                                           metadata_len=metadata_len, encoding=encoding)
            grids.append(data)
    grids_merged = np.stack(grids)
    return metadata, grids_merged




# Evolution du volume et du débit à l'exutoire du réseau
def get_outfall_network_flow(path_to_drainage: str, time_step_minute: int|float) -> pd.DataFrame:
    """Get the variations of the outfall flow for the .rpt file in the Drainage directory using swmm_api 

    Args:
        path_to_drainage (str): Path to the Drainage outputs
        time_step_minute (int, optional): time step of the reports in minutes. 

    Raises:
        FileNotFoundError: The path to the drainage directory or report file is wrong

    Returns:
        pd.DataFrame: A DataFrame with columns : <br> outfall node, volume_m3, time_min, name, Q_m3/s, time_h, volume_cumul_m3

    """
    # Initialisation of a df
    df=pd.DataFrame()
    path_list = []
    # Getting all the path to the files in drainage dir
    if not os.path.exists(path_to_drainage):
        raise FileNotFoundError(f"The directory {path_to_drainage} does not exist.")
    for file in os.listdir(path_to_drainage):
        if not os.path.exists(path_to_drainage):
            raise FileNotFoundError(f"The file {file} does not exist.")
        path_list.append(os.path.join(path_to_drainage, file))
    # Sorting in natural key so file.1 -> file.2 -> file.10
    sorted_path_list = sorted(path_list, key= lambda x: natural_key(x))
    # For each .rtp file
    for i in range(len(sorted_path_list)):
        path = sorted_path_list[i]
        rpt = read_rpt_file(path)
        ols = rpt.outfall_loading_summary['Total_Volume_10^6 ' + rpt.unit.VOL2] * 1000 # L to m^3
        ols = pd.DataFrame(ols)
        # Column for time in minute
        ols["time_min"] = time_step_minute * (i+1) # the first report is after the first loop
        ols = ols.apply(pd.to_numeric)
        ols["name"] = os.path.basename (path ) 
        df= pd.concat([df, ols])
    df.reset_index(inplace=True)
    df.columns = ["outfall node", "volume_m3", "time_min", "name"]
    df["Q_m3/s"] = df["volume_m3"] / time_step_minute / 60
    # Column for time in hours
    df["time_h"] = df["time_min"] / 60
    # Compute cumulative volume
    df["volume_cumul_m3"] = df["volume_m3"].cumsum()
    return df


def read_overland_stats(path_to_overland_stats: str) -> dict:
    """Read the information inside the overland_sumary.stats file

    Args:
        path_to_overland_stats (str): path to the overland_sumary.stats file. Usually "Outputs\Stat\overland_summary.stats"

    Returns:
        dict: Dictionnary regrouping the information of the overland_summary_stats
    """
    with open(path_to_overland_stats, "r") as f:
        overland_sum_stats = [line.strip() for line in f.readlines()]
    overland_sum_stats = [line for line in overland_sum_stats if ".=" in line]
    overland_sum_stats = [line.split("=")  for line in overland_sum_stats ]
    overland_sum_stats_dict = dict(overland_sum_stats)
    overland_sum_stats_dict = {key.replace(".", ""): float(value) for key,value in overland_sum_stats_dict.items()}
    return overland_sum_stats_dict


def get_input_timeseries(path_to_inp_files: str, report_number: int) -> list[pd.DataFrame]:
    """Create a list of dataframe containing informations about the TIMESERIES part of the .inp files.

    Args:
        path_to_inp_files (str): Path to the directory of the .inp files. <br> Usually 
        report_number (int): number of the last report to include in the function.

    Returns:
        list[pd.DataFrame]: List of dataframe related to each .inp files in the directory. <br> Colums of the dataframes are: <br> 'time_serie' <br> 'time' <br> 'flow'
    """
    list_df = []
    for i in range(1,report_number+1):
        with open(path_to_inp_files + rf"\swmm{i}.inp", 'r') as f:
            ts_lines = []
            lire_ts = False
            for line in f:
                if line.strip() == '[TIMESERIES]':
                    lire_ts = True
                    continue
                if lire_ts and line.strip().startswith('['):
                    break  # Arrêter à la prochaine section
                if lire_ts and line.strip() and not line.startswith(';'):
                    ts_lines.append(line.strip())

        df_time_serie = pd.DataFrame([ligne.split() for ligne in ts_lines], columns=['time_serie', "time", "flow"], dtype=float)
        df_time_serie = df_time_serie.loc[df_time_serie["time"] != 0., :]
        df_time_serie["vol_m3"] = df_time_serie["time"] * df_time_serie['flow'] * 3600  # h * m3/s * 60 *60 -> m3
        list_df.append(df_time_serie)
    return list_df

