import ploting
import read_file
import pandas
import numpy
import data_handling

soil_path = r"Inputs\soils.asc"
surface_path = r"Inputs\Surface_input_2018.txt"
elev_path = r"Inputs\elev.asc"
drainage_path = r"Outputs\Drainage"
drainage_input_path = r"Inputs\Drainage_input.txt"

meta_soil, grid_soil = read_file.read_asc_file(file_path=soil_path, ignore_first_line=True)
meta_elev, grid_elev = read_file.read_asc_file(file_path=elev_path, ignore_first_line=True)

dict_luse = read_file.create_dict_luse(file_path=surface_path)
# print(dict_luse)

map_soil = ploting.create_plotly_map_soil(grid=grid_soil, metadata=meta_soil, dict_luse=dict_luse)
map_elev = ploting.create_plotly_map(grid=grid_elev, metadata=meta_elev, unit=["Elevation", "m"], grids_hover=[grid_soil], info_hover=["Soil type"] )
# map_soil.show()
# infiltdepth_paths = [fr"Outputs\Grids\Infiltration\infiltdepth.{i}" for i in range(0, 361)]
# raindepth_paths = [fr"Outputs\Grids\Rain\raindepth.{i}" for i in range(0, 361)]
# meta_infiltdepth, grids_infiltdepth = read_file.get_timed_grid(infiltdepth_paths, ignore_first_line=False)
# meta_raindepth, grids_raindepth = read_file.get_timed_grid(raindepth_paths, ignore_first_line=False)
# print(meta_infiltdepth)
# map_infildepth = ploting.create_animated_map(grids_infiltdepth, metadata=meta_infiltdepth)
# map_raindepth = ploting.create_animated_map(grids_raindepth, metadata=meta_raindepth,
#                                             time_step=3, time_step_unit="minutes",
#                                             grids_hover=[grid_elev, grid_soil], info_hover=["Elev (m)", "Soil type"],
#                                             unit=["Rain depth", "mm"], fig_dim=(1000,1000))


df_outfall = read_file.get_outfall_network_flow(drainage_path, time_step_minute=3)


df_nodes = read_file.get_nodes_coord(drainage_input_path)
df_conduits = read_file.get_conduits(drainage_input_path)

map_network = ploting.create_network_map(df_conduits, df_nodes, bg_map=map_elev, fig_dim=(1000,1000) )
# map_network.show()

# ploting.show_errors(map_elev, meta_elev, [[62, 150]]).show()
# print(meta_elev)
path_stats=r"Outputs\Stat\overland_summary.stats"
dict_stats = read_file.read_overland_stats(path_stats)

path_inp = r"Inputs\MHDC"
list_df_timeseries = read_file.get_input_timeseries(path_inp, 360)

path_drainage = r"Outputs\Drainage"
df_outfall = read_file.get_outfall_network_flow(path_drainage, 3)
path_infildepth_360 = r"Outputs\Grids\Infiltration\infiltdepth.360"
meta_infiltdepth, grid_infiltdepth360 = read_file.read_asc_file(file_path=path_infildepth_360, ignore_first_line=False)
gully_house_mask = data_handling.create_mask_luse(dict_luse, grid_soil, names_to_mask=["Gully", 'House'])

data_handling.compute_water_balance(dict_stats, meta_elev, 
                                    df_outfall, 
                                    grid_infiltdepth360, gully_house_mask, list_df_timeseries )





