import numpy as np
from scipy import ndimage

def cor_elev_pb(
    elev_grid: np.ndarray, diff_max: float, nb_max: int = 0, max_iter: int = 10, mask_size: tuple[int, int] = (3,3), ignore_center: bool=True) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Corrige itérativement les pixels aberrants dans une grille d'élévation.
    Un pixel est considéré comme aberrant si sa valeur est inférieure à (moyenne des voisins - diff_max).
    La correction est répétée jusqu'à ce qu'il reste au plus `nb_max` pixels aberrants, ou que `max_iter` itérations soient atteintes.

    Args:

        elev_grid (np.ndarray): Grille 2D d'élévations.
        diff_max (float): Seuil maximal autorisé entre un pixel et la moyenne de ses voisins.
        nb_max (int): Nombre maximal de pixels aberrants acceptés pour arrêter la boucle. Par défaut, 0.
        max_iter (int): Nombre maximal d'itérations. Par défaut, 10.
        mask_size (tuple[int, int]): Taille du mask pour le calcul de la moyenne. Par défaut (3,3)
        ignore_center (bool): Ignorer le pixel central pour le calul de la moyenne du mask
        

    Returns:

        tuple[np.ndarray, np.ndarray, int]:
            - elev_pb: Masque booléen final des pixels aberrants (True = aberrant).
            - elev_cor: Grille corrigée.
            - iter: Nombre d'itérations effectuées.
    """
    # Masque pour les 8 voisins (exclut le centre)
    mask = np.ones(mask_size, dtype=bool)
    if ignore_center:
        mask[1,1] = False 

    # Initialisation
    elev_cor = elev_grid.copy()  # Évite de modifier l'entrée
    iter_count = 0
    nb_aberrants = elev_grid.size  # Initialise à une valeur > nb_max
    # Boucle de correction
    while nb_aberrants > nb_max and iter_count < max_iter:
        iter_count += 1
        # test_init = elev_cor[103][63]
        mean_elev = ndimage.generic_filter(elev_cor, np.nanmean, footprint=mask, mode='constant', cval=np.nan)
        test=elev_cor[103][63]
        # test_mean = mean_elev[103][63]
        # Identification des pixels aberrants
        elev_pb = elev_cor <= (mean_elev - diff_max)
        # test_pb = elev_pb[103][63]
        nb_aberrants = elev_pb.sum()
        # Correction : remplace les pixels aberrants par la moyenne de leurs voisins
        elev_cor = np.where(elev_pb, mean_elev, elev_cor)
        test_cor = elev_cor[103][63]
        # print(f"init : {test_init}, mean : {test_mean}, pb : {test_pb}, cor: {test_cor} ")
        # fig = ploting.create_plotly_map(elev_pb.astype(int), meta ,"Différence >0.4m", grids_hover=[elev_init], info_hover=["elev"], color="blues")
        # fig = ploting.create_plotly_map(elev_cor, meta ,"Différence >0.4m", grids_hover=[elev_init], info_hover=["elev"], color="rainbow")
        # fig.show()
        print("Iter ", iter_count, "  ", nb_aberrants, " pixels aberrants")

    return elev_pb, elev_cor, iter_count