import re
import numpy as np
import read_file 
import pandas as pd
import json

def natural_key(s):
    """For natural sorting """
    return [int(x) if x.isdigit() else x.lower()for x in re.split(r'(\d+)', s)]


def create_mask_luse(dict_soil: dict[int, dict[str, any]], soil_grid: np.array, names_to_mask: list[str]) -> np.array:
    """Create a mask of the luse grid where pixel with values associated to names to mask are True, others are False
    Args:
        dict_soil (dict[int, dict[str, any]]): A dictionary where keys are soil IDs and values are dictionaries
                                   containing soil parameters (conduction, cap_suction, moisture_def, 
                                   name, manning, intercept_depth).
        soil_grid (np.array): 2D numpy array of the luse or soils data
        names_to_mask (list[str]): List of the luse names to mask

    Returns:
        np.array: 2D numpy array of the luse or soils data where pixels related to names to mask are Ture, others are False
    """
    ncol = soil_grid.shape[1]
    nrow = soil_grid.shape[0]
    mask_glob = np.full((nrow, ncol), 0) # On crée le mask avec des 0
    for name in names_to_mask:  # Pour chaque nom à masquer oin crée un mask qui repère avec 1
        num_to_mask = [id for id in dict_soil.keys() if dict_soil[id]["name"] == name][0]
        mask = soil_grid.copy()
        mask[mask != num_to_mask] = 0
        mask[mask == num_to_mask] = 1
        mask_glob = mask_glob + mask
        mask_glob = mask_glob.astype(bool) # Le masf final est TRUE à tous les emplacements ou les noims sont repérés
    return  mask_glob


def compute_water_balance(overland_stats: dict, metadata:dict,  
                          df_outfall: pd.DataFrame, 
                          last_infilt_grid: np.array,
                          luse_mask_to_swmm: np.array,
                          list_df_timeseries_inp: list[pd.DataFrame],
                          info: str=None,
                          save_file: str=None
                         ) -> dict:
    """_summary_

    Args:

        overland_stats (dict): _description_
        metadata (dict): _description_
        df_outfall (pd.Dataframe): _description_
        last_infilt_grid (np.array): _description_
        luse_mask_to_swmm (np.array): _description_
        list_df_timeseries_inp (list[pd.DataFrame]): _description_
        list_SfN (list[str]): _description_
        save_file (str): Name of the text file to store the water balance

    Returns:

        dict: _description_
    """
    cell_size = metadata["cellsize"]
    # Reading the overland summary .stats dict
    gross_rain = overland_stats["Cumulative Gross Rainfall Volume Entering Domain (m3)"]
    interception = overland_stats["Cumulative Interception Volume Within Domain (m3)"]
    net_rain = overland_stats["Cumulative Net Rainfall Volume Entering Domain (m3)"]
    exess_rain = overland_stats["Cumulative Rainfall Excess (Rain-Intercept-Infilt) (m3)"]
    V_out = overland_stats["Volume leaving the Watershed, V_out (m3)"]
    V_infilt_tot = overland_stats["Volume Infiltrated Overland, V_inf (m3)"]
    V_excess = overland_stats["Cumulative Rainfall Excess (Rain-Intercept-Infilt) (m3)"]
    V_runoff = overland_stats["Volume leaving the Watershed via Overland Flow (m3)"]
    V_stag = V_excess - V_runoff
    print("------------------------------------------------------\n"
        f"Overland_stats TREX : \n"
        "------------------------------------------------------\n"
        f"Gross rain : {gross_rain} m3 \n"
      f"Interception : {interception} m3\n"
      f"Net rain : {net_rain} m3\n"
      f"V_out (infiltration + overland flow) : {V_out} m3\n"
      f"Infiltration total : {V_infilt_tot} m3\n"
      f"Overland flow : {V_runoff} m3\n"
      f"V_surf : {V_stag.round(2)} m3\n"
      f"Verif {(net_rain-V_infilt_tot-V_runoff-V_stag).round(2)} = 0")
    
    
    to_swmm_grid = last_infilt_grid * luse_mask_to_swmm # Keeping only pixels related to swmm
    infiltration_true_grid = last_infilt_grid * ~luse_mask_to_swmm # Keeping pixels really infiltrated in the ground
    V_infilt_true = np.nansum(infiltration_true_grid) * cell_size**2
    V_to_swmm = np.nansum(to_swmm_grid) * cell_size**2
    print("------------------------------------------------------\n"
        f"Infiltration depth map TREX : \n"
        "------------------------------------------------------\n"
        f"Volume true infiltration : {V_infilt_true.round(2)} m3\n"
        f"Exclusion des pixels de luse_mask_to_swmm : \n"
        f"Voume infiltration to SWMM : {V_to_swmm.round(2)} m3")

    list_vol = []
    for df in list_df_timeseries_inp:
        list_vol.append(df["vol_m3"].sum())
    V_timeseries = sum(list_vol).round(2)
    V_outfall = df_outfall["volume_m3"].sum()
    V_water_lost_swmm = V_timeseries - V_outfall
    print("------------------------------------------------------\n"
          f"Inputs & Outputs SWMM: \n"
          "------------------------------------------------------\n"
        f"Somme des volumes timeseries (m3) : {V_timeseries}\n"
        f"Somme volume outfall (m3) :         {V_outfall}\n"
        f"Eau perdue dans SWMM (m3) :         {V_water_lost_swmm.round(2)}\n")
    
    water_balance = dict(gross_rain=gross_rain,
                interception=interception,
                net_rain=net_rain,
                V_runoff=V_runoff,
                V_stag=V_stag,
                V_infilt_tot=V_infilt_tot,
                V_infilt_true=V_infilt_true,
                V_to_swmm=V_to_swmm,
                V_timeseries=V_timeseries,
                V_outfall=V_outfall
                )
    
    if save_file:
        with open(f"{save_file}.txt", "w") as file:
            file.write(json.dumps(water_balance))

    return dict(gross_rain=gross_rain,
                interception=interception,
                net_rain=net_rain,
                V_runoff=V_runoff,
                V_stag=V_stag
                V_infilt_tot=V_infilt_tot,
                V_infilt_true=V_infilt_true,
                V_to_swmm=V_to_swmm,
                V_timeseries=V_timeseries,
                V_outfall=V_outfall
                )

def write_asc_file(file_name: str, metadata: dict, grid: np.array, title: str, nan_value: int = -9999, format: str='%.3f') -> None:
    """Creation of a .asc file to use with Multi-Hydro

    Args:
        file_name (str): Name of the file to write
        metadata (dict): dictionary containing spatial metadata for the grid. Must include:
            - 'xllcorner': x-coordinate of the lower-left corner.
            - 'yllcorner': y-coordinate of the lower-left corner.
            - 'cellsize': Size of each grid cell.
            - 'ncols': Number of columns in the grid.
            - 'nrows': Number of rows in the grid.
            - 'NODATA_value': Value related to no data
        grid (np.array): 2D grid of data
        title (str): first line of the file
        nan_value (int, optional): Value to write instead of Nan. Defaults to -9999.
        format (str, optional): Format uuse to write de data. Defaults to %.3f
    
    Notes:
        - Some MH input data MUST have a title line at the begining of the file. Refere to MH documentation.
    
    Returns:
        None
    """

    # --- Prepare header ---
    header_lines = [
        f"ncols         {metadata['ncols']}",
        f"nrows         {metadata['nrows']}",
        f"xllcorner     {metadata['xllcorner']}",
        f"yllcorner     {metadata['yllcorner']}",
        f"cellsize      {metadata['cellsize']}",
        f"NODATA_value  {metadata['NODATA_value']}"
    ]

     # Add title if provided (some MH inputs require it)
    if title:
        header_lines.insert(0, title)
    header = "\n".join(header_lines) + "\n"
    grid_write = grid.copy()
    grid_write = np.nan_to_num(grid_write, nan=nan_value)
    with open(file_name, 'w') as f:
        f.write(header)  # Write header
        np.savetxt(f, grid_write, fmt=format, delimiter=' ', newline='\n')
    print (f"{file_name} as been created")
    return None


