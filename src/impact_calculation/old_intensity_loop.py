def _intensity_loop(self, uni_ev, coord, res_centr, num_centr):
    """Compute and intensity matrix. For each event, if more than one points of
    data have the same coordinates, take the sum of days below threshold
    of these points (duration as accumulated intensity).

    Parameters:
        uni_ev (list): list of unique cluster IDs
        coord (list): Coordinates as in Centroids.coord
        res_centr (float): Geographical resolution of centroids
        num_centroids (int): Number of centroids

    Returns:
        intensity_mat (sparse.lilmatrix): intensity values as sparse matrix
    """


    stps = list(np.arange(0, len(uni_ev) - 1, INTENSITY_STEP)) + [len(uni_ev)]

    if len(stps) == 1:
        intensity_list = []
        for cl_id in uni_ev:
            intensity_list.append(
                self._intensity_one_cluster(tree_centr, cl_id,
                                            res_centr, num_centr))
        return sparse.csr_matrix(intensity_list)

    for idx, stp in enumerate(stps[0:-1]):
        if not idx:
            intensity_list = []
            for cl_id in uni_ev[0:stps[1]]:
                intensity_list.append(
                    self._intensity_one_cluster(tree_centr, cl_id,
                                                res_centr, num_centr))
            intensity_mat = sparse.csr_matrix(intensity_list)
        else:
            intensity_list = []
            for cl_id in uni_ev[stp:stps[idx + 1]]:
                intensity_list.append(
                    self._intensity_one_cluster(tree_centr, cl_id,
                                                res_centr, num_centr))
            intensity_mat = sparse.vstack((intensity_mat,
                                           sparse.csr_matrix(intensity_list)))
    return intensity_mat
