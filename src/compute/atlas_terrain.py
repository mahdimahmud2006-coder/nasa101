"""HAND candidate routing on an audited downstream graph."""
import numpy as np


def height_above_drainage(dem, receivers, contributing_area, downstream_first, threshold_m2):
    """Use unfilled EGM96 elevations and mask paths ending at open outlets."""
    elevation = np.asarray(dem).ravel()
    area = np.asarray(contributing_area).ravel()
    links = np.asarray(receivers).ravel()
    order = np.asarray(downstream_first)
    if (len(area)!=len(elevation) or len(links)!=len(elevation) or not np.isfinite(threshold_m2)
        or threshold_m2<=0 or links.dtype.kind not in 'iu' or order.dtype.kind not in 'iu'
        or np.any((links < -1)|(links >= len(links)))):
        raise ValueError('One bounded downstream graph and a positive drainage threshold required')
    valid = np.isfinite(elevation) & np.isfinite(area)
    if not np.array_equal(np.sort(order),np.flatnonzero(valid)):
        raise ValueError('Routing order must cover each valid cell exactly once')
    rank = np.full(len(links),-1,dtype=int)
    rank[order] = np.arange(len(order))
    linked = valid & (links>=0)
    if np.any(rank[links[linked]]>=rank[linked]):
        raise ValueError('Receivers must precede donors in the routing order')
    drainage = np.full(len(links),-1,dtype=int)
    boundary = np.zeros(len(links),bool)
    for cell in order:
        downstream = links[cell]
        if downstream == -1:
            boundary[cell] = True
        elif valid[downstream]:
            if area[cell] >= threshold_m2:
                drainage[cell] = cell
            else:
                drainage[cell] = drainage[downstream]
                boundary[cell] = boundary[downstream]
    resolved = drainage>=0
    heights = np.full(len(links),np.nan)
    heights[resolved] = elevation[resolved]-elevation[drainage[resolved]]
    negative = heights<0
    heights[negative] = np.nan
    return heights.reshape(np.shape(dem)), {
        'assessed':int(np.isfinite(heights).sum()),'masked':int((~valid).sum()),
        'boundaryAffected':int(boundary.sum()),'negativeHeight':int(negative.sum()),
        'unresolved':int((valid&~resolved&~boundary).sum()),
    }
