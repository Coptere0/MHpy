import numpy as np
import pandas as pd
import os
from typing import Optional
import re
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

#### Création des autres cartes 
def create_plotly_map(grid: np.array, metadata: dict, 
                      title: str = "Titre", color: str = 'blues_r', fig_dim: tuple = (None, None), 
                      unit: list = ["Data", "unit"], 
                      grids_hover: np.array = None, info_hover: list =None) -> go.Figure:
    """Create an interactive heatmap with continuous colorbar using Plotly, based on a 2D grid and spatial metadata.
    The x and y axes represent geographic coordinates, while the hover information includes pixel indices
    Additional grids can be provided to enrich hover information (e.g., land use, interception depth).
    
    Args:
        grid (np.ndarray):
            2D array representing the data to be visualized.
        metadata (dict):
            dict_soilnary containing spatial metadata for the grid. Must include:
            - 'xllcorner': x-coordinate of the lower-left corner.
            - 'yllcorner': y-coordinate of the lower-left corner.
            - 'cellsize': Size of each grid cell.
            - 'ncols': Number of columns in the grid.
            - 'nrows': Number of rows in the grid.
        title (str, optional):
            Title of the plot. Defaults to "Titre".
        color (str, optional):
            Color scale for the heatmap. Defaults to 'blues_r'.
        fig_dim (tuple, optional):
            Figure dimensions as (width, height). Defaults to (None, None).
        unit (list, optional):
            List containing the data label and unit (e.g., ["Elevation", "m"]).
            Defaults to ["Data", "unit"].
        grids_hover (list of np.ndarray, optional):
            List of additional 2D grids to include in hover information.
            Each grid must match the shape of `grid`. Defaults to None.
        info_hover (list of str, optional):
            List of labels for the additional hover information.
            Must match the number of grids in `grids_hover`. Defaults to None.
    
    Notes:
        - Pixel indices in the hover information start at 1 (to match TREX conventions).
        - If `grids_hover` is provided, `info_hover` must have the same number of elements.
        - The y-axis is reversed to match cartographic conventions (y increases upwards).
        - Not suited for ploting the land use map.

    Returns:
        go.Figure: A Plotly Figure object containing the interactive heatmap.
    """
    # Coordination spatiale
    x0 = metadata['xllcorner']
    y0 = metadata['yllcorner']
    dx = metadata['cellsize']
    nx = metadata['ncols']
    ny = metadata['nrows']
    x = np.linspace(x0, x0 + nx * dx, nx)
    y = np.linspace(y0, y0 + ny * dx, ny)
    # Inversion des valeurs de y 
    y = y[::-1]
    # Valeurs extrèmes pour la colorbar
    maxi = np.nanmax(grid)
    mini = np.nanmin(grid)
    # Pour le hover indices des pixels
    rows, cols = np.indices(grid.shape)
    customdata_test = np.dstack((rows +1, cols +1)) # adding 1 to match the way TREX count (starting to 1)
    # Adding the hovers grids to customdata
    if grids_hover:
        for grid_h in grids_hover:
            customdata_test = np.dstack((customdata_test, grid_h))
    # Création de la fig
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=grid,
            zmax=maxi, zmin=mini,
            x=x, y=y,
            customdata=customdata_test,
            hovertemplate=f"<b>{unit[0]}:" +" %{z:.2f}" + f" {unit[1]}<extra></extra></b><br>"+
                            "Ligne: %{customdata[0]}<br>" +
                            "Colonne: %{customdata[1]}<br>",
            colorscale=color
        )
    )
    # Ajout des informations supplémentaires pour chaque grille dans grids_hover
    if grids_hover and info_hover:
         # Récupération du hovertemplate de base
        base_hovertemplate = fig.data[0].hovertemplate
        for i, info in enumerate(info_hover, start=2):
            base_hovertemplate += f"{info}: %"+ "{customdata[" + f"{i}]" + "}<br>" # Weird syntax to match plotly needs
        # Mise à jour du hovertemplate
        fig.data[0].hovertemplate = base_hovertemplate
    fig.update_layout(
        title=title,
        autosize = False,
        width=fig_dim[0],
        height=fig_dim[1],
        xaxis_title="X (m)",
        xaxis=dict(
        tickformat=" d",  # Affiche les entiers 
        tickmode='auto',
        showgrid=True
        ),
        yaxis_title="Y (m)",
        yaxis=dict(
        tickformat=" d",  # Affiche les entiers
        tickmode='auto',
        showgrid=True
        ),
        )
    fig.update_yaxes(scaleanchor="x")
    fig.update_coloraxes(colorbar=dict(nticks=10, ticks="outside",ticklen=6, ))
    
    return fig


#### Création de la carte d'occupation des sols
def create_plotly_map_soil(grid: np.array, metadata: dict, dict_luse: dict,
                                   title: str = "Soil type", fig_dim: tuple = (None, None), 
                                   palette=['#3a7535', "#FFB428", "#5A5A5A", "#00B1BE", "#13b604", "#ff1707", '#7a807a']) -> go.Figure:
    """Create an interactive heatmap of the soil type, based on a 2D grid and spatial metadata.
    The x and y axes represent geographic coordinates, while the hover information includes pixel indices.

    Args:
        grid (np.array): 2D array representing the data to be visualized.
        metadata (dict): 
            dicti0nary containing spatial metadata for the grid. Must include:
                - 'xllcorner': x-coordinate of the lower-left corner.
                - 'yllcorner': y-coordinate of the lower-left corner.
                - 'cellsize': Size of each grid cell.
                - 'ncols': Number of columns in the grid.
                - 'nrows': Number of rows in the grid.
        dict_luse (dict):  
            dictionary where keys are soil IDs and values are dictionaries containing soil parameters 
            (conduction, cap_suction, moisture_def, name, manning, intercept_depth).
            Given by create_dict_ground function
        title (str, optional): 
            Title of the figure. Defaults to "Soil type".
        fig_dim (tuple, optional): 
            Figure dimensions as (width, height). Defaults to (None, None).
        palette (list, optional): 
            Palete of color to use in the figure. 
            Defaults to ['#3a7535', "#FFB428", "#5A5A5A", "#00B1BE", "#13b604", "#ff1707", '#7a807a']
            for 1.Forest 2.House 3.Road 4.Water 5.Grass 6.Gully 7.Impervious surface.
    
    Notes:
        - Pixel indices in the hover information start at 1 (to match TREX conventions).
        - The y-axis is reversed to match cartographic conventions (y increases upwards).
        
        - Not suited for ploting the lkand use map.

    Returns:
        go.Figure: A Plotly Figure object containing the interactive heatmap.
    """        
    # Coordination spatiale
    x0 = metadata['xllcorner']
    y0 = metadata['yllcorner']
    dx = metadata['cellsize']
    nx = metadata['ncols']
    ny = metadata['nrows']
    x = np.linspace(x0, x0 + nx * dx, nx)
    y = np.linspace(y0, y0 + ny * dx, ny)
    # Inversion des valeurs de y 
    y = y[::-1]
    max_key = max(dict_luse.keys())
    # Pour le hover indices des pixels
    rows, cols = np.indices(grid.shape)
    customdata_test = np.dstack((rows +1, cols +1)) # adding 1 to match the way TREX count (starting to 1)
    # Construire une color scale DISCRÈTE
    colorscale = []
    for i in dict_luse:
        c = palette[i-1] # soil indice starts at 1
        colorscale.append(((i-1)/max_key, c))
        colorscale.append((i/max_key, c))
    # Création de la figure
    fig = go.Figure()
    # Ajout de la heatmap occupation des sols
    fig.add_trace(
        go.Heatmap(
        z=grid,
        x=x,
        y=y,
        colorscale=colorscale,
        zmin=1,
        zmax=max_key,
        showscale=False,
        customdata=customdata_test,
        hovertemplate="<b>Soil type :  %{z}<extra></extra></b><br>"+
                            "Ligne: %{customdata[0]}<br>" +
                            "Colonne: %{customdata[1]}<br>",
        )
    )
    # Ajout d’une légende catégorielle à part
    for i in dict_luse:
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=14, color=palette[i-1]),
                name=dict_luse[i]['name'],
                hoverinfo="skip"
            )
        )
    fig.update_layout(
        title=title,
        autosize=False,
        width=fig_dim[0],
        height=fig_dim[1],
        xaxis_title="X (m)",
        xaxis=dict(
        tickformat=" d",  # Affiche les entiers 
        tickmode='auto',
        showgrid=True
        ),
        yaxis_title="Y (m)",
        yaxis=dict(
        tickformat=" d",  # Affiche les entiers
        tickmode='auto',
        showgrid=True
        ),
        legend=dict(
            title=title,       # titre de la légende (facultatif)
            x=1,                    # position horizontale (1.02 = juste à droite du graphique)
            y=0.2,                       # position verticale (1 = haut)
            xanchor="right",            # ancrage horizontal de la légende
            yanchor="bottom",             # ancrage vertical de la légende
            bgcolor="rgba(0,0,0,0.5)",  # fond blanc semi-transparent
            bordercolor="black",
            borderwidth=1
        )
    )

    fig.update_yaxes(scaleanchor="x")
    return fig


def create_animated_map(grids: list[np.array], metadata: dict, 
                          title: str="Titre", color: str='blues_r', fig_dim: tuple[int, int]=(None, None), 
                          unit: list=["Data", "unit"], 
                          time_step=None, time_step_unit: str="loop", 
                          grids_hover: np.array = None, info_hover: list =None) -> go.Figure:
    """Creates an animated heatmap from a list of 2D grids, with optional hover information and a time slider.

    Args:
        grids (list[np.array]): A list of 2D NumPy arrays representing the data to animate. 
            Each array corresponds to a frame in the animation
        metadata (dict): A dictionary containing spatial metadata for the grids. Must include:
            - 'xllcorner': x-coordinate of the lower-left corner.
            - 'yllcorner': y-coordinate of the lower-left corner.
            - 'cellsize': size of each grid cell.
            - 'ncols': number of columns in the grid.
            - 'nrows': number of rows in the grid.
        title (str, optional): Title of the figure. Defaults to "Titre".
        color (str, optional): Color scale for the heatmap. Defaults to 'blues_r'.
        fig_dim (tuple[int, int], optional): Figure dimensions as (width, height). Defaults to (None, None).
        unit (list, optional): Unit information for the hover template, as [data_name, data_unit].Defaults to ["Data", "unit"].
        time_step (_type_, optional): Time increment between frames. If None, frames are labeled by index. Defaults to None.
        time_step_unit (str, optional): Unit of the time step (e.g., "seconds", "hours"). Defaults to "loop".
        grids_hover (np.array, optional): Additional 2D arrays to display in the hover template. Defaults to None.
        info_hover (list, optional): Labels for the additional hover data. Must match the number of arrays in `grids_hover`.
            Defaults to None.

    Returns:
        go.Figure: A Plotly Figure object representing the animated heatmap.
    
    Examples:
    >>> metadata = {'xllcorner': 0, 'yllcorner': 0, 'cellsize': 1, 'ncols': 10, 'nrows': 10}
    >>> grids = [np.random.rand(10, 10) for _ in range(5)]
    >>> fig = create_animated_map(grids, metadata, title="Simulation", time_step=1, time_step_unit="hour")
    >>> fig.show()

    Notes:
        - The `grids` and `grids_hover` arrays must have the same spatial dimensions.
        - The `info_hover` list must have the same length as the number of arrays in `grids_hover`.
        - The `time_step` parameter is used to label the animation frames with actual time values.
    """
    # Coordination spatiale
    x0 = metadata['xllcorner']
    y0 = metadata['yllcorner']
    dx = metadata['cellsize']
    nx = metadata['ncols']
    ny = metadata['nrows']
    x = np.linspace(x0, x0 + nx * dx, nx)
    y = np.linspace(y0, y0 + ny * dx, ny)
    # Inversion des valeurs de y 
    y = y[::-1]
    # Valeurs extrèmes pour la colorbar
    maxi = np.nanmax(grids[-1])
    print(maxi)
    mini = np.nanmin(grids[0])
    # Pour le hover indices des pixels
    rows, cols = np.indices(grids[0].shape)
    customdata_test = np.dstack((rows +1, cols +1)) # adding 1 to match the way TREX count (starting to 1)
    # Adding the hovers grids to customdata
    if grids_hover:
        for grid_h in grids_hover:
            customdata_test = np.dstack((customdata_test, grid_h))
    # Creation of time increment
    times = [i for i in range(len(grids))] # Time is the frame number
    if time_step:
        times = [i * time_step for i in times] # Time is the simulation time
    # Création de la fig
    fig = go.Figure(
        data=go.Heatmap(
            z=grids[0],
            zmax=maxi, zmin=mini,
            x=x, y=y,
            customdata=customdata_test,
            hovertemplate=f"<b>{unit[0]}:" +" %{z:.2f}" + f" {unit[1]}<extra></extra></b><br>"+
                            "Ligne: %{customdata[0]}<br>" +
                            "Colonne: %{customdata[1]}<br>",
            colorscale=color,
            ),
        frames=[go.Frame(data=go.Heatmap(z=grids[i]), name = str(times[i])) for i in range(len(times))]
    )
    # Ajout des informations supplémentaires pour chaque grille dans grids_hover
    if grids_hover and info_hover:
         # Récupération du hovertemplate de base
        base_hovertemplate = fig.data[0].hovertemplate
        for i, info in enumerate(info_hover, start=2):
            base_hovertemplate += f"{info}: %"+ "{customdata[" + f"{i}]" + "}<br>" # Weird syntax to match plotly needs
        # Mise à jour du hovertemplate
        fig.data[0].hovertemplate = base_hovertemplate
    # Adding the slider
    sliders = [{
    "active": 0,
    "currentvalue": {
        "prefix": f"Temps ({time_step_unit}) = ",
        "visible": True
    },
    "steps": [
        {
            "label": str(times[i]),
            "method": "animate",
            "args": [
                [str(times[i])],
                {"mode": "immediate", "frame": {"duration": 0}, "transition": {"duration": 0}}
            ]
        }
        for i in range(len(times))
    ]
}]
    fig.update_layout(
        title=title,
        autosize = False,
        width=fig_dim[0],
        height=fig_dim[1],
        xaxis_title="X (m)",
        xaxis=dict(
        tickformat=" d",  # Affiche les entiers 
        tickmode='auto',
        showgrid=True
        ),
        yaxis_title="Y (m)",
        yaxis=dict(
        tickformat=" d",  # Affiche les entiers
        tickmode='auto',
        showgrid=True
        ),
        sliders=sliders,
        )
    fig.update_yaxes(scaleanchor="x")
    fig.update_coloraxes(colorbar=dict(nticks=10, ticks="outside",ticklen=6, ))
    
    return fig


### Création de la carte de réseau d'assainissement
def create_network_map(df_conduits: pd.DataFrame, df_nodes: pd.DataFrame, 
                       bg_map: go.Figure=None, show_node_id: bool=False, 
                       title: str="Réseau", fig_dim: tuple[int|None, int|None]= (None, None))-> go.Figure:
    """Plot the nsewer network map using **networkx**

    Args:
        df_conduits (pd.DataFrame): Dataframe of the conduits of the sewer network with a least 2 columns: <br>- *From_Node* for the start node <br>- *To_Node* for the end node
        df_nodes (pd.DataFrame): Dataframe of the nodes of the sewer network with a least 3 columns: <br>- *Node* for the node Id <br>- *X* for the x coordinates <br>- *Y* for the y coordinates}
        bg_map (go.Figure, optional): Background map, usualy the mask. Defaults to None.
        show_node_id (bool, optional): Show the nodes id on the figure. Defaults to False.
        title (str, optional): Title of the figure. Defaults to "Réseau".

    Returns:
        go.Figure: Map of the sewer network
    """
    # Usinf the background map
    if bg_map is None:
        fig = go.Figure()
    else:
        fig = go.Figure(bg_map)
    # Graph creation
    G = nx.Graph()
    # Add nodes position
    for _, row in df_nodes.iterrows():
        G.add_node(row['Node'], pos=(row['X'], row['Y']))
    # Ajouter conduits
    for _, conduit in df_conduits.iterrows():
        G.add_edge(conduit['From_Node'], conduit['To_Node'])
    pos = nx.get_node_attributes(G, "pos")
    # --- 3. Traces conduits : lignes (Scatter) ---
    edge_x = []
    edge_y = []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    fig.add_trace(go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(color="red", width=1),
        hoverinfo="none",
        name="Conduits",
    ))
    # --- 4. Traces nœuds ---
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(size=5, color="blue"),
        name="Nœuds",
        hovertext=[str(n) for n in G.nodes()],
        hoverinfo="text"
    ))
    # --- 5. Traces labels si demandé ---
    if show_node_id:
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode="text",
            text=[str(int(n)) for n in G.nodes()],
            textposition="top right",
            textfont=dict(size=8, color="black"),
            name="Labels"
        ))

    # --- 6. Ajustements généraux ---
    fig.update_layout(
        showlegend=False,
        autosize = False,
        width=fig_dim[0],
        height=fig_dim[1],
        xaxis_title="X (m)",
        xaxis=dict(
        tickformat=" d",  # Affiche les entiers 
        tickmode='auto',
        showgrid=True
        ),
        yaxis_title="Y (m)",
        yaxis=dict(
        tickformat=" d",  # Affiche les entiers
        tickmode='auto',
        showgrid=True
        ),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title=title
    )
    fig.update_yaxes(scaleanchor="x")

    return fig




def create_hydrogramme(df_rain: pd.DataFrame, list_df_outfall: list[pd.DataFrame], 
                       legend_rain: str="Legend rain", legends_outfall: list[str]=None,
                       axis_title: list[str]=["Axe x", "Axe y1", "axe y2"],
                       max_range_rain: float=None, max_range_outfall: float=None,
                       x_range: list[float]=None, bar_width: float=None,
                       title: str=None, fig_dim: tuple[int, int]=(None, None)) -> go.Figure:
    """Creates a hydrogram plot combining rainfall data and outfall discharge data on a dual-axis chart.
    The rainfall data is displayed as bars on a secondary (inverted) y-axis, while outfall data is shown as line traces on the primary y-axis.

    Args:
        df_rain (pd.DataFrame): DataFrame containing rainfall data. Expected columns: [time, rainfall].
        list_df_outfall (list[pd.DataFrame]): List of DataFrames, each containing outfall discharge data. Expected columns: [time, discharge].
        legend_rain (str, optional): Legend label for the rainfall data. Defaults to "Legend rain".
        legends_outfall (list[str], optional): List of legend labels for each outfall DataFrame. If None, defaults to ["Legend output 1", "Legend output 2", ...].
        axis_title (list[str], optional): List of titles for the x-axis, primary y-axis, and secondary y-axis. Defaults to ["Axe x", "Axe y1", "axe y2"].
        max_range_rain (float, optional):  Maximum value for the rainfall y-axis range. If None, uses 1.1 * max rainfall value.
        max_range_outfall (float, optional): Maximum value for the outfall y-axis range. If None, auto-scales. Defaults to None.
        x_range (list[float], optional): Range of the x-axis. If None, auto-range.
        bar_width (float, optional): Width of the rain bars. Default to None.
        title (str, optional): Title of the plot. If None, no title is displayed. Defaults to None.
        fig_dim (tuple[int, int], optional): Dimensions of the figure as (width, height). Defaults to (None, None).

    Returns:
        go.Figure: A Plotly Figure object containing the hydrogram plot with dual y-axes.

    Example:
        >>> import pandas as pd
        >>> import plotly.graph_objects as go
        >>> df_rain = pd.DataFrame({"time": [1, 2, 3], "rainfall": [10, 20, 15]})
        >>> df_outfall1 = pd.DataFrame({"time": [1, 2, 3], "discharge": [5, 10, 8]})
        >>> df_outfall2 = pd.DataFrame({"time": [1, 2, 3], "discharge": [3, 6, 4]})
        >>> fig = create_hydrogramme(df_rain, [df_outfall1, df_outfall2], legends_outfall=["Outfall A", "Outfall B"])
        >>> fig.show()
    """
    
    fig = go.Figure()
    if not legends_outfall:
        legends_outfall = [f"Legend output {i}" for i in range(1, len(list_df_outfall)+1)]
    # Plotting the outputs
    for df, legend in zip(list_df_outfall, legends_outfall):
        cols_output = df.columns
        print("columns : ", [x for x in cols_output])
        fig.add_trace(
            go.Scatter(
                x=df[cols_output[0]],
                y=df[cols_output[1]],
                name=legend,            
            ),
        )
    # Ajout de la courbe de précipitations (axe Y secondaire, inversé)
    cols_rain = df_rain.columns
    max_rain = max_range_rain if max_range_rain else df_rain[cols_rain[1]].max()*1.1
    fig.add_trace(
        go.Bar(
            x=df_rain[cols_rain[0]],
            y=df_rain[cols_rain[1]],
            name=legend_rain,
            showlegend=True,
            yaxis="y2",
            width=bar_width,
        ),
    )
    fig.update_layout(
        title=title,
        width=fig_dim[0],
        height=fig_dim[1],
        template="plotly_white",
        yaxis=dict(
            range=[0, max_range_outfall] if max_range_outfall else None, # Échelle synchronisée (optionnel)
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            title=axis_title[1],
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
        ),
        yaxis2=dict(
            range=[max_rain, 0], # Échelle synchronisée (optionnel)
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            title=axis_title[2],
            overlaying="y",
            side="right",  # Place l'axe y à droite
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
            position=1,
            linecolor='black',
            linewidth=0.5
        ),
        xaxis=dict(
            range=x_range if x_range else[0, df_rain[cols_rain[0]].max() *1.1],
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
            title=axis_title[0],
            showgrid=True,
            gridcolor='lightgrey',
            gridwidth=1,
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)"
        )
    )
    return fig


def show_errors(map: go.Figure, metadata: dict, 
                pixel_indices: list[list[int, int]], color: str='red' ) -> go.Figure:
    """Highlights specific pixels on a Plotly map figure to indicate errors or areas of interest.
    The function overlays a heatmap on the input map, marking the specified pixels with a given color.

    Args:
        map (go.Figure): A Plotly Figure object representing the map to be annotated.
        metadata (dict): A dictionary containing spatial metadata for the map. Expected keys: <br> - 'xllcorner': x-coordinate of the lower-left corner. <br> - 'yllcorner': y-coordinate of the lower-left corner. <br> - 'cellsize': Size of each pixel in map units.<br> - 'ncols': Number of columns (x-direction) in the map.<br> - 'nrows': Number of rows (y-direction) in the map.
        pixel_indices (list[list[int, int]]): List of pixel indices to highlight. Each index is a list of [row, column].
        color (str, optional): _description_. Defaults to 'red'.

    Returns:
        go.Figure: A new Plotly Figure object with the original map and highlighted pixels.
            The title of the figure is updated to include "!!! ERREUR !!!".
    
    Attention:
        The pixel indices are the ones given by TreX (first pixel of the map is [1, 1])

    """

    # Coordination spatiale
    x0 = metadata['xllcorner']
    y0 = metadata['yllcorner']
    dx = metadata['cellsize']
    nx = metadata['ncols']
    ny = metadata['nrows']

    # Duplication de la carte pour ne pas modifier l'originale
    new_map = go.Figure(map)
    title = new_map.layout.title.text + " !!! ERREUR !!!"
    pixel_grid = np.zeros((ny, nx))

    x = np.linspace(x0, x0 + nx * dx, nx)
    y = np.linspace(y0, y0 + ny * dx, ny)
    y = y[::-1]
    for pixel in pixel_indices:
        pixel_row = pixel[0] - 1  # Python indices start at 0, TreX start a 1
        pixel_col = pixel[1] - 1 # Python indices start at 0, TreX start a 1
        pixel_grid[pixel_row, pixel_col] = 1

        x_pixel = x0 + (pixel_col)  * dx
        y_pixel = y0 + (ny - pixel_row) * dx

        new_map.add_trace(
        go.Heatmap(
            z=pixel_grid,
            x=x,
            y=y,
            colorscale=[[0., "rgba(0,0,0,0)"], [1, color]],
            showscale=False,
            hoverinfo="skip" ))

    new_map.update_layout(title=title)

    return new_map

