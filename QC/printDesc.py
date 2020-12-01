import json

def printDesc(dataDesc, specs):

    struct= '<h3><b>BSE</b></h3>\n' \
            'autoBSE = {autoBSE}<br>\n' \
            'diffusion iterations= = {diffusionIterations}<br>\n' \
            'diffusionc constant = {diffusionConstant}<br>\n' \
            'edgeDetection constant = {edgeDetectionConstant}<br>\n' \
            'skip BSE = {skipBSE}<br>\n ' \
            '<h3><b>BFC</b></h3>\n' \
            'iterative mode = {iterativeMode}<br>\n ' \
            '<h3><b>PVC</b></h3>\n spatial prior = {spatialPrior}<br>\n ' \
            '<h3><b>Cerebrum</b></h3>\n' \
            'cost function = {costFunction}<br>\n use centroids = {useCentroids}<br>\n ' \
            'linear convergence = {linearConvergence}<br>\n' \
            'warp convergence = {warpConvergence}<br>\n warp level = {warpLevel}<br>\n ' \
            '<h3><b>Inner cortex</b></h3>\n tissue frraction threshold = {tissueFractionThreshold}<br>\n ' \
            '<h3><b>SVReg</b></h3>\n' \
            'atlas = {atlas}<br>\n single thread = {singleThread}<br>\n cache folder = {cacheFolder}<br>\n' \
            '<h3><b>Smoothing level</b></h3>\n ' \
            'smooth surf = {smoothSurf}<br>' \
            'smooth vol = {smoothVol}<br>'.format(
        autoBSE=specs.autoParameters,
        diffusionIterations=specs.diffusionIterations,
        diffusionConstant=specs.diffusionConstant,
        edgeDetectionConstant=specs.edgeDetectionConstant,
        skipBSE=specs.skipBSE,
        iterativeMode=specs.iterativeMode,
        spatialPrior=specs.spatialPrior,
        costFunction=specs.costFunction,
        useCentroids=specs.useCentroids,
        linearConvergence=specs.linearConvergence,
        warpConvergence=specs.warpConvergence,
        warpLevel=specs.warpLevel,
        tissueFractionThreshold=specs.tissueFractionThreshold,
        atlas=specs.atlas,
        singleThread=specs.singleThread,
        cacheFolder=specs.cache,
        smoothSurf = specs.smoothsurf,
        smoothVol = specs.smoothvol

    )

    print(struct)


    bdp = ''.format(

    )

    func = ''.format(

    )

    datadesc = json.load(open(dataDesc))


    for key, value in datadesc.items():
        desc = '<h3><b>{0}</b></h3>\n{1}<br>\n'.format(key, value)
        print(desc)