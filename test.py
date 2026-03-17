import ploting
import read_file
import pandas
import numpy as np
import data_handling
import os

#######################################
#    Reading the general input file   #
####################################### 
del_folder = None
general_input_path = r"Inputs\general_input.txt"
general_input = read_file.read_general_input(file_path=general_input_path)
sim_name = general_input["Simulation_name"]
time_step_h = float(general_input["loop_duration"])
surface_path = general_input["Surface_File"]
drainage_input_path = general_input["Drainage_File"]
new_folder = False
new_path = fr"analyse_{sim_name}"
if not os.path.exists(new_path):
    new_folder = True
    print(f"Création du dossier {new_path}")
    os.makedirs(new_path)
else:
    del_folder = input(f"Le dossier {new_path} existe déjà, voulez vous continuer ? Y/N").lower()

if del_folder == "y" or new_folder:
    print("""
    #######################################\n
    #       Reading the surface file      #\n
    #######################################\n""")
    # Inputs
    input_paths, output_paths  = read_file.get_inputoutput_files_path(surface_path)
    soil_path = input_paths["SOIL_TYPES"]
    luse_path = input_paths["LANDUSE"]
    elev_path = input_paths["ELEVATION"]
    mask_path = input_paths["MASK"]
    storage_path = input_paths["STORAGE_DEPTHS"]
    initial_overland_path = input_paths["INITIAL_WATER_OVERLAND"]
    initial_infiltration_path = input_paths["INITIAL_INFILTRATION"]
    # Outputs
    water_export_path = output_paths["WATEREXPORT"]
    rainfall_rate_path = output_paths["RAINFALL_RATE"]
    rainfall_depth_path = output_paths["RAINFALL_DEPTH"]
    infiltration_rate_path = output_paths["INFILTRATION_RATE"]
    infiltration_depth_path = output_paths["INFILTRATION_DEPTH"]
    water_discharge_path = output_paths["WATER_DISCHARGE"]
    water_depth_path = output_paths["WATER_DEPTH"]
    mass_balance_path = output_paths["MASS_BALANCE"]
    sum_stat_path = output_paths["SUMMARY_STATISTICS"]

    #######################################
    #     Reading the input map files     #
    ####################################### 
    print("* Reading the input map files \n")
    # Mask map
    meta_mask, grid_mask = read_file.read_asc_file(file_path=mask_path, ignore_first_line=True)
    # Soils map
    meta_soil, grid_soil = read_file.read_asc_file(file_path=soil_path, ignore_first_line=True)
    # Landuse map
    meta_luse, grid_luse = read_file.read_asc_file(file_path=luse_path, ignore_first_line=True)
    # Elevation map
    meta_elev, grid_elev = read_file.read_asc_file(file_path=elev_path, ignore_first_line=True)

    #######################################
    #          Ploting input maps         #
    #######################################
    print( "* Exporting the input map \n")
    # Mask map
    map_mask = ploting.create_plotly_map(grid=grid_mask , metadata=meta_mask, unit=["Elevation", "m"], fig_dim=(1000,1000), title=f"Mask map {sim_name}" )
    map_mask.write_html(rf"{new_path}\map_mask.html")
    # SOILS MAP #
    dict_luse = read_file.create_dict_luse(file_path=surface_path)
    palette = ['#3a7535', "#9E711E", "#73C263", "#8D8D8D", "#ffc935", "#359b06", '#7a807a']
    map_soil = ploting.create_plotly_map_soil(grid=grid_soil, metadata=meta_soil, dict_luse=dict_luse, fig_dim=(1000,1000), palette=palette, title=f"Soil map {sim_name}")
    map_soil.write_html(rf"{new_path}\soil_map.html")
    # Elevation map
    map_elev = ploting.create_plotly_map(grid=grid_elev, metadata=meta_elev, unit=["Elevation", "m"], grids_hover=[grid_soil], info_hover=["Soil type"], fig_dim=(1000,1000), title=f"Elev map {sim_name}" )
    map_elev.write_html(rf"{new_path}\map_elev.html")
    
    #######################################
    #     Reading the output map files    #
    #######################################
    print( "* Reading the output map files \n")
    # Rainfall depth
    path = "/".join(rainfall_depth_path.split("/")[:-1])
    key = rainfall_depth_path.split("/")[-1]
    raindepth_paths = [rf"{path}/{file}" for file in os.listdir(path) if key in file]
    meta_raindepth, grids_raindepth = read_file.get_timed_grid(raindepth_paths, ignore_first_line=False)
    # Infiltration depth
    path = "/".join(infiltration_depth_path.split("/")[:-1])
    key = infiltration_depth_path.split("/")[-1]
    infiltdepth_paths = [rf"{path}\{file}" for file in os.listdir(path) if key in file]
    meta_infiltdepth, grids_infiltdepth = read_file.get_timed_grid(infiltdepth_paths, ignore_first_line=False)
        # gully_house_mask = data_handling.create_mask_luse(dict_luse, grid_soil, names_to_mask=[ 'House'])
        # grids_infiltdepth_mask = [grid *~ gully_house_mask for grid in grids_infiltdepth ]
    # Water depth
    path = "/".join(water_depth_path.split("/")[:-1])
    key = water_depth_path.split("/")[-1]
    waterdepth_paths = [rf"{path}\{file}" for file in os.listdir(path) if key in file]
    meta_waterdepth, grids_waterdepth = read_file.get_timed_grid(waterdepth_paths, ignore_first_line=False)
    # Water discharge
    path = "/".join(water_discharge_path.split("/")[:-1])
    key = water_discharge_path.split("/")[-1]
    waterdis_paths = [rf"{path}\{file}" for file in os.listdir(path) if key in file]
    meta_waterdis, grids_waterdis = read_file.get_timed_grid(waterdis_paths, ignore_first_line=False)

    #######################################
    #          Ploting output maps        #
    #######################################
    print( "* Exporting the input map \n")
    # Rainfall depth
    map_raindepth = ploting.create_animated_map(grids_raindepth, metadata=meta_raindepth, fig_dim=(1000,1000),
                                                 unit=["Rain depth", "mm"], time_step=time_step_h*60, time_step_unit="minutes",
                                                 )
    map_raindepth.write_html(rf"{new_path}/raindepth_map.html")
    # Infiltration depth
    map_infildepth = ploting.create_animated_map(grids_infiltdepth, metadata=meta_infiltdepth, fig_dim=(1000,1000), 
                                                unit=["Infiltdepth", "m"], time_step=time_step_h*60, time_step_unit="minutes", 
                                                grids_hover=[grid_soil, grid_elev], info_hover=["Soil", "Elev"],
                                                )
    map_infildepth.write_html(rf"{new_path}/infildepth_map.html")
    # Water depth
    map_waterdepth = ploting.create_animated_map(grids_waterdepth, metadata=meta_infiltdepth, fig_dim=(1000,1000), 
                                                unit=["Waterdepth", "m"], time_step=time_step_h*60, time_step_unit="minutes", 
                                                grids_hover=[grid_soil, grid_elev], info_hover=["Soil", "Elev"],
                                                )
    map_waterdepth.write_html(rf"{new_path}\waterdepth_map.html")
    # Water discharge
    map_waterdis = ploting.create_animated_map(grids_waterdis, metadata=meta_infiltdepth, fig_dim=(1000,1000), 
                                                unit=["Waterdis", "?"], time_step=time_step_h*60, time_step_unit="minutes", 
                                                grids_hover=[grid_soil, grid_elev], info_hover=["Soil", "Elev"],
                                                )
    map_waterdis.write_html(rf"{new_path}\water_dis_map.html")
    
    # df_outfall = read_file.get_outfall_network_flow(drainage_path, time_step_minute=3)


    # df_nodes = read_file.get_nodes_coord(drainage_input_path)
    # df_conduits = read_file.get_conduits(drainage_input_path)

    # map_network = ploting.create_network_map(df_conduits, df_nodes, bg_map=map_mask, fig_dim=(1000,1000) )

    # map_network.write_html(rf"map_network.html")

    # # ploting.show_errors(map_elev, meta_elev, [[62, 150]]).show()
    # # print(meta_elev)
    # path_stats=r"Outputs\Stat\overland_summary.stats"
    # dict_stats = read_file.read_overland_stats(path_stats)

    # path_inp = r"Inputs\MHDC"
    # list_df_timeseries = read_file.get_input_timeseries(path_inp, 360)

    # path_drainage = r"Outputs\Drainage"
    # df_outfall = read_file.get_outfall_network_flow(path_drainage, 3)
    # path_infildepth_360 = r"Outputs\Grids\Infiltration\infiltdepth.360"
    # meta_infiltdepth, grid_infiltdepth360 = read_file.read_asc_file(file_path=path_infildepth_360, ignore_first_line=False)
    # gully_house_mask = data_handling.create_mask_luse(dict_luse, grid_soil, names_to_mask=["Gully", 'House'])

    # data_handling.compute_water_balance(dict_stats, meta_elev, 
    #                                     df_outfall, 
    #                                     grid_infiltdepth360, gully_house_mask, list_df_timeseries )

    # print(df_outfall.head())

    # df_rain = read_file.get_rain_serie(file_path=surface_path)
    # print(df_rain.head())
    # hydrograph = ploting.create_hydrogramme(df_rain.loc[:, ["time", "intensity_mm/h"]], [df_outfall.loc[:, ["time_h", "Q_m3/s"]]], legend_rain="Précipitation",
    #                                         legends_outfall=["Débit à l'exutoire"], axis_title=["Temps", "Débit (m3/s)", "Précipitation (mm)"],
    #                                         max_range_rain=80, max_range_outfall=4,
    #                                         fig_dim=(2000, 1000))
    # hydrograph.write_html(rf"hydrograph.html")






    # elev_ecole = grid_elev[66:95, 95:126]
    # print(elev_ecole)
    # map_elev_ecole = ploting.create_plotly_map(grid=elev_ecole, metadata=meta_elev)
    # map_elev_ecole.show()

    # _, grid_lidar = read_file.read_asc_file(r"Inputs\elev_bon.asc")
    # map_lidar = ploting.create_plotly_map(grid_lidar, meta_elev, title="Elev LIiDAR", fig_dim=(1000,1000))
    # map_lidar.write_html("elev_lidar.html")

    # _, grid_lidar_bat = read_file.read_asc_file(r"Inputs\elev_up.asc")
    # map_lidar_bat = ploting.create_plotly_map(grid_lidar_bat, meta_elev, title="Elev LIiDAR + bat up", fig_dim=(1000,1000))
    # map_lidar_bat.write_html("elev_lidar_bat.html")

    # print(np.nanmax(grids_infiltdepth))