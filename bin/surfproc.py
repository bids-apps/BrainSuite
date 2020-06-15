try:
    import vtk
    VTK_INSTALLED = 1
except ImportError as e:
    VTK_INSTALLED = 0

import numpy as np
from scipy.sparse.linalg import cg  # ,spilu,LinearOperator
from scipy.sparse import eye, spdiags, csc_matrix, vstack  # , diags
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.tri as mtri
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource


if VTK_INSTALLED:
    from vtk import (vtkSphereSource, vtkPolyData, vtkDecimatePro, vtkPoints,
                     vtkCleanPolyData, vtkCellArray,
                     vtkPolyDataConnectivityFilter, vtkSmoothPolyDataFilter,
                     vtkPolyDataNormals, vtkCurvatures, vtkUnsignedCharArray)
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

    from vtk import (vtkRenderer, vtkRenderWindow, vtkPolyDataMapper,
                     vtkInteractorStyleTrackballActor, VTK_MAJOR_VERSION,
                     vtkRenderWindowInteractor, vtkActor, vtkPolyDataNormals,
                     vtkWindowToImageFilter, vtkPNGWriter)

from dfsio import readdfs, writedfs
import scipy as sp
#from mayavi import mlab
#import trimesh as tm

__author__ = "Anand A. Joshi"
__copyright__ = "University of Southern California, Los Angeles"
__email__ = "ajoshi@usc.edu"

#import matplotlib.pyplot as plt
import matplotlib.cm as cmx
import matplotlib.colors as colors


def surf_weight(surf1):
    X = surf1.vertices[:, 0]
    Y = surf1.vertices[:, 1]
    Z = surf1.vertices[:, 2]
    NumTri = surf1.faces.shape[0]
    #    NumVertx = X.shape[0]
    vertx_1 = surf1.faces[:, 0]
    vertx_2 = surf1.faces[:, 1]
    vertx_3 = surf1.faces[:, 2]
    V1 = np.column_stack((X[vertx_1], Y[vertx_1], Z[vertx_1]))
    V2 = np.column_stack((X[vertx_2], Y[vertx_2], Z[vertx_2]))
    V3 = np.column_stack((X[vertx_3], Y[vertx_3], Z[vertx_3]))
    x1 = np.zeros((NumTri))
    y1 = np.zeros((NumTri))
    v2_v1temp = V2 - V1
    x2 = np.linalg.norm(v2_v1temp, axis=1)
    y2 = np.zeros((NumTri))
    x3 = np.einsum('ij,ij->i', (V3 - V1), (v2_v1temp / np.column_stack(
        (x2, x2, x2))))
    mynorm = np.cross((v2_v1temp), V3 - V1, axis=1)
    yunit = np.cross(mynorm, v2_v1temp, axis=1)
    y3 = np.einsum('ij,ij->i', yunit,
                   (V3 - V1)) / np.linalg.norm(yunit, axis=1)
    sqrt_DT = (np.abs((x1 * y2 - y1 * x2) + (x2 * y3 - y2 * x3) +
                      (x3 * y1 - y3 * x1)))
    Ar = 0.5 * (np.abs((x1 * y2 - y1 * x2) + (x2 * y3 - y2 * x3) +
                       (x3 * y1 - y3 * x1)))

    TC = face_v_conn(surf1)
    Wt = (1.0 / 3.0) * (TC)
    # Wt = sp.sparse.spdiags(Wt*Ar, (0), NumTri, NumTri)
    surf_weight = sp.sqrt(Wt * Ar)
    return surf_weight


def patch_color_labels(s, freq=[1], cmap='Paired', shuffle=True):
    ''' color by freq of labels '''
    s.vColor = sp.zeros(s.vertices.shape)
    _, labels = sp.unique(s.labels, return_inverse=True)
    labels += 1
    colr = get_cmap(sp.amax(labels) + 1, cmap=cmap)
    s.vColor = s.vColor + 1
    perm1 = sp.mod(3511 * sp.arange(sp.amax(labels) + 1), sp.amax(labels) + 1)
    freq = sp.reshape(freq, (len(freq), 1))
    if shuffle == True:
        s.vColor = (1 - freq) + freq * sp.array(colr(perm1[labels])[:, :3])
    else:
        s.vColor = (1 - freq) + freq * sp.array(colr(labels)[:, :3])
    return s


def patch_color_attrib(s, values=[], cmap='jet', clim=[0]):
    ''' color by freq of labels '''
    if len(values) == 0:
        values = s.attributes
    if len(clim) == 1:
        vmin = sp.amin(values)
        vmax = sp.amax(values)
    else:
        vmin = clim[0]
        vmax = clim[1]

    s.vColor = sp.zeros(s.vertices.shape)
    color_norm = colors.Normalize(vmin=vmin, vmax=vmax)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=cmap)
    s.vColor = scalar_map.to_rgba(values)
    s.vColor = s.vColor[:, :3]
    return s


def get_cmap(N, cmap='jet'):
    '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct
    RGB color.'''
    color_norm = colors.Normalize(vmin=0, vmax=N - 1)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=cmap)

    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)

    return map_index_to_rgb_color


def face_areas(s):
    r12 = s.vertices[s.faces[:, 0], :]
    r13 = s.vertices[s.faces[:, 2], :] - r12
    r12 = s.vertices[s.faces[:, 1], :] - r12
    area1 = sp.sqrt(sp.sum(sp.cross(r12, r13)**2, axis=1)) / 2.0
    return area1


def smooth_surf_function(s, f0, a1=3.1, a2=3.1, aniso=None, normalize=0):

    if aniso is None:
        aniso = np.ones((len(s.vertices), 1))

    S, Dx, Dy = get_stiffness_matrix_tri_wt(s, aniso)
    M = vstack((a1 * S, a2 * vstack((Dx, Dy))))
    A = vstack((eye(len(s.vertices)), M))
    b = np.concatenate((f0, np.zeros(M.shape[0])))
    AtA = A.T * A

    M = spdiags(1.0 / AtA.diagonal(), [0], AtA.shape[0], AtA.shape[1])
    #    M=np.diag(np.diag(A.transpose()*A))
    f, nits = cg(AtA, A.T * b, tol=1e-100, maxiter=600, M=M)
    #    print('f',f)
    if normalize > 0:
        f = f * np.linalg.norm(f0) / np.linalg.norm(f)

    return f


def get_stiffness_matrix_tri_wt(surf1, W):
    W = np.squeeze(W)
    X = surf1.vertices[:, 0]
    Y = surf1.vertices[:, 1]
    Z = surf1.vertices[:, 2]
    NumTri = surf1.faces.shape[0]
    #    NumVertx = X.shape[0]
    vertx_1 = surf1.faces[:, 0]
    vertx_2 = surf1.faces[:, 1]
    vertx_3 = surf1.faces[:, 2]
    V1 = np.column_stack((X[vertx_1], Y[vertx_1], Z[vertx_1]))
    V2 = np.column_stack((X[vertx_2], Y[vertx_2], Z[vertx_2]))
    V3 = np.column_stack((X[vertx_3], Y[vertx_3], Z[vertx_3]))
    x1 = np.zeros((NumTri))
    y1 = np.zeros((NumTri))
    v2_v1temp = V2 - V1
    x2 = np.linalg.norm(v2_v1temp, axis=1)
    y2 = np.zeros((NumTri))
    x3 = np.einsum('ij,ij->i', (V3 - V1), (v2_v1temp / np.column_stack(
        (x2, x2, x2))))
    mynorm = np.cross((v2_v1temp), V3 - V1, axis=1)
    yunit = np.cross(mynorm, v2_v1temp, axis=1)
    y3 = np.einsum('ij,ij->i', yunit,
                   (V3 - V1)) / np.linalg.norm(yunit, axis=1)
    sqrt_DT = (np.abs((x1 * y2 - y1 * x2) + (x2 * y3 - y2 * x3) +
                      (x3 * y1 - y3 * x1)))
    Ar = 0.5 * (np.abs((x1 * y2 - y1 * x2) + (x2 * y3 - y2 * x3) +
                       (x3 * y1 - y3 * x1)))
    #    Ar=1.0+0.0*Ar
    y1 = y1 / sqrt_DT
    y2 = y2 / sqrt_DT
    y3 = y3 / sqrt_DT
    x1 = x1 / sqrt_DT
    x2 = x2 / sqrt_DT
    x3 = x3 / sqrt_DT
    tmp_A = np.concatenate((y2 - y3, y3 - y1, y1 - y2), axis=0)
    tmp_B = np.concatenate((x3 - x2, x1 - x3, x2 - x1), axis=0)

    rowno = np.arange(0, NumTri)
    rowno_all = np.concatenate((rowno, rowno, rowno))
    vertx_all = np.concatenate((vertx_1, vertx_2, vertx_3))
    Dx = csc_matrix((tmp_A, (rowno_all, vertx_all)), (NumTri, len(X)))
    Dy = csc_matrix((tmp_B, (rowno_all, vertx_all)), (NumTri, len(X)))

    TC = face_v_conn(surf1)
    Wt = (1.0 / 3.0) * (TC.T * W)
    Wt = spdiags(Wt * Ar, (0), NumTri, NumTri)
    S = Dx.T * Wt * Dx + Dy.T * Wt * Dy

    return S, Dx, Dy


def face_v_conn(FV):

    nFaces = FV.faces.shape[0]
    #    nVertices = FV.vertices.shape[0]

    rows = np.concatenate((FV.faces[:, 0], FV.faces[:, 1], FV.faces[:, 2]))
    cols = np.concatenate(
        (np.arange(0, nFaces), np.arange(0, nFaces), np.arange(0, nFaces)))
    data = np.ones((len(rows)))
    TriConn = csc_matrix((data, (rows, cols)))

    return TriConn


if VTK_INSTALLED:
    def mkVtkIdList(it):
        vil = vtk.vtkIdList()
        for i in it:
            vil.InsertNextId(int(i))
        return vil


    def close_window(iren):
        render_window = iren.GetRenderWindow()
        render_window.Finalize()
        iren.TerminateApp()


    def createPolyData(verts, faces):

        poly = vtkPolyData()

        points = vtkPoints()
        for i in range(0, verts.shape[0]):
            points.InsertPoint(i, verts[i, ])


    #    points.SetData(numpy_to_vtk(verts))

        poly.SetPoints(points)

        tri = vtkCellArray()
        for i in range(0, faces.shape[0]):
            tri.InsertNextCell(3)
            tri.InsertCellPoint(faces[i, 0])
            tri.InsertCellPoint(faces[i, 1])
            tri.InsertCellPoint(faces[i, 2])

        poly.SetPolys(tri)

        return poly


    def reducepatch(surf, ratio=0.90, VERBOSITY=0):
        ratio = 1.0 - ratio
        pol = createPolyData(surf.vertices, surf.faces)

        decimate = vtkDecimatePro()
        decimate.SetInputConnection(pol.GetProducerPort())
        decimate.SetTargetReduction(ratio)
        decimate.Update()

        decimatedPoly = vtkPolyData()
        decimatedPoly.ShallowCopy(decimate.GetOutput())

        connectivity2 = vtkPolyDataConnectivityFilter()
        connectivity2.SetInput(decimatedPoly)
        connectivity2.SetExtractionModeToLargestRegion()
        connectivity2.Update()
        decimatedPoly = connectivity2.GetOutput()

        cleaner = vtkCleanPolyData()
        cleaner.SetInput(decimatedPoly)
        cleaner.Update()
        decimatedPoly = cleaner.GetOutput()

        if VERBOSITY > 0:
            print("\n # extracted regions: " +
                str(connectivity2.GetNumberOfExtractedRegions()))
            print("Before decimation: " + str(pol.GetNumberOfPoints()) +
                " points;" + str(pol.GetNumberOfPolys()) + " polygons.")
            print("After decimation: " + str(decimatedPoly.GetNumberOfPoints()) +
                " points;" + str(decimatedPoly.GetNumberOfPolys()) +
                " polygons .")

        pts = decimatedPoly.GetPoints()
        surf.vertices = vtk_to_numpy(pts.GetData())
        faces1 = decimatedPoly.GetPolys()
        f1 = faces1.GetData()
        f2 = vtk_to_numpy(f1)
        f2 = f2.reshape(len(f2) / 4, 4)
        surf.faces = f2[:, 1:]

        return surf


    def vtkpoly2Surf(vtkp):
        pts = vtkp.GetPoints()

        class surf:
            pass

        surf.vertices = vtk_to_numpy(pts.GetData())
        faces1 = vtkp.GetPolys()
        f1 = faces1.GetData()
        f2 = vtk_to_numpy(f1)
        f2 = f2.reshape(len(f2) // 4, 4)
        surf.faces = f2[:, 1:]
        return surf


    def add_normals(s1):
        normals = vtkPolyDataNormals()
        normals.SetInput(createPolyData(s1.vertices, s1.faces))
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        normals.SplittingOff()
        normals.Update()
        normals.AutoOrientNormalsOn()
        normals.ConsistencyOn()
        # normals.Update()
        n1 = normals.GetOutput()
        p1 = n1.GetPointData()
        s1.normals = vtk_to_numpy(p1.GetNormals())
        s1.vertices = vtk_to_numpy(n1.GetPoints().GetData())
        faces = vtk_to_numpy(n1.GetPolys().GetData())
        faces = faces.reshape(len(faces) / 4, 4)
        s1.faces = faces[:, 1:]

        return s1


    def mean_curvature(s):
        curve1 = vtkCurvatures()
        s = createPolyData(s.vertices, s.faces)
        curve1.SetInput(s)
        curve1.SetCurvatureTypeToMean()
        curve1.Update()
        m = curve1.GetOutput()
        m = vtk_to_numpy(m.GetPointData().GetScalars())
        return m


    def get_sphere(center=[0, 0, 0], radius=5.0, res=100):
        source = vtkSphereSource()
        source.SetCenter(center[0], center[1], center[2])
        source.SetRadius(radius)
        source.SetThetaResolution(res)
        source.SetPhiResolution(res)
        source.Update()
        surf1 = source.GetOutput()
        pts = surf1.GetPoints()
        vert1 = vtk_to_numpy(pts.GetData())
        faces1 = surf1.GetPolys()
        f1 = faces1.GetData()
        f2 = vtk_to_numpy(f1)
        f2 = f2.reshape(len(f2) / 4, 4)

        class surf:
            pass

        surf.faces = f2[:, 1:]
        surf.vertices = vert1
        return surf


    #from PIL import Image


    def view_patch_vtk(r, azimuth=90, elevation=0, roll=-90, outfile=0, show=1):

        c = r.vColor
        ro = r
        r = createPolyData(r.vertices, r.faces)

        Colors = vtkUnsignedCharArray()
        Colors.SetNumberOfComponents(3)
        Colors.SetName("Colors")

        for i in range(len(ro.vertices)):
            Colors.InsertNextTuple3(255 * c[i, 0], 255 * c[i, 1], 255 * c[i, 2])

        r.GetPointData().SetScalars(Colors)
        r.Modified()
        # ##    r.Update()
        # mapper
        mapper = vtkPolyDataMapper()
        if VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(r)
        else:
            #       mapper.SetInputConnection(r.GetOutputPort())
            mapper.SetInputData(r)

        actor = vtkActor()
        actor.SetMapper(mapper)
        #    actor.GetProperty().SetInterpolationToPhong()
        normals = vtkPolyDataNormals()
        normals.SetInputData(r)
        normals.ComputePointNormalsOn()
        normals.ComputeCellNormalsOn()
        #normals.SplittingOff()
        normals.AutoOrientNormalsOn()
        normals.ConsistencyOn()
        #normals.SetFeatureAngle(4.01)
        normals.Update()
        mapper.SetInputData(normals.GetOutput())

        ren = vtkRenderer()
        renWin = vtkRenderWindow()
        renWin.SetSize(1600, 1600)
        #    renWin.SetDPI(200)
        if show == 0:
            renWin.SetOffScreenRendering(1)

        renWin.AddRenderer(ren)
        # create a renderwindowinteractor
        iren = vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)
        ren.SetBackground(256.0 / 256, 256.0 / 256, 256.0 / 256)

        ren.AddActor(actor)

        # enable user interface interactor
        iren.Initialize()

        renWin.Render()
        ren.GetActiveCamera().Azimuth(azimuth)
        ren.GetActiveCamera().Elevation(elevation)
        ren.GetActiveCamera().Roll(roll)
        renWin.Render()
        #  windowToImageFilter->SetInput(renderWindow);
        #  windowToImageFilter->SetMagnification(3); //set the resolution of the output image (3 times the current resolution of vtk render window)
        #  windowToImageFilter->SetInputBufferTypeToRGBA(); //also record the alpha (transparency) channel
        #  windowToImageFilter->ReadFrontBufferOff(); // read from the back buffer
        #  windowToImageFilter->Update();

        if outfile != 0:
            w2i = vtkWindowToImageFilter()
            writer = vtkPNGWriter()
            #        iren.SetDPI(200)
            w2i.SetInput(renWin)
            w2i.SetInputBufferTypeToRGBA()
            w2i.ReadFrontBufferOff()
            w2i.Update()
            writer.SetInputData(w2i.GetOutput())
            writer.SetFileName(outfile)
            iren.Render()
            writer.Write()


    #        image = Image.open(outfile)
    #        image.load()
    ##        imageSize = image.size
    #        imageBox = image.getbbox()
    #        print(image.getbbox())
    #        cropped = image.crop(imageBox)
    #        print(cropped.getbbox())
    #        cropped.save(outfile)

        if show != 0:
            iren.Start()

        close_window(iren)
        del renWin, iren


    def axisEqual3D(ax):
        extents = np.array(
            [getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
        sz = extents[:, 1] - extents[:, 0]
        centers = np.mean(extents, axis=1)
        maxsize = max(abs(sz))
        r = maxsize / 2
        for ctr, dim in zip(centers, 'xyz'):
            getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)


    def readdfsVTK(fname):
        s = readdfs(fname)
        poly = createPolyData(s.vertices, s.faces)
        return poly


    def smooth_patch(surf, iterations=15, relaxation=0.1):
        smoothFilter = vtkSmoothPolyDataFilter()
        smoothFilter.SetInputData(createPolyData(surf.vertices, surf.faces))
        smoothFilter.SetNumberOfIterations(iterations)
        smoothFilter.SetRelaxationFactor(relaxation)
        smoothFilter.Update()
        surf1 = smoothFilter.GetOutput()
        pts = surf1.GetPoints()
        vert1 = vtk_to_numpy(pts.GetData())
        faces1 = surf1.GetPolys()
        f1 = faces1.GetData()
        f2 = vtk_to_numpy(f1)
        f2 = f2.reshape(int(len(f2) / 4), 4)

        class surf2(surf):
            pass

        surf2.faces = f2[:, 1:]
        surf2.vertices = vert1
        return surf2


''' from vispy import scene
from vispy.color import Color
from vispy import gloo
from vispy.scene.cameras import TurntableCamera
import vispy.io
import vispy.geometry
import ply
import sys

def view_patch_vispy(r, attrib=[], opacity=1, fig=0, show=1, colorbar=1, clim=[0], outfile=0, azimuth=0, elevation=-90, colormap='jet'):
    meshdata = vispy.geometry.MeshData(vertices=r.vertices, faces=r.faces, vertex_colors=r.vColor)
    canvas = scene.SceneCanvas(keys='interactive', size=(800, 600), show=True)
    mesh = scene.visuals.Mesh(meshdata=meshdata, shading='smooth')
    view = canvas.central_widget.add_view()
    view.add(mesh)
    view.bgcolor = '#efefef'
    view.camera = TurntableCamera(azimuth=azimuth, elevation=elevation)
    color = Color("#3f51b5")
#    mesh.set_gl_state('translucent', depth_test=True, cull_face=True)
    axis = scene.visuals.XYZAxis(parent=view.scene)
    if __name__ == '__main__' and sys.flags.interactive == 0:
        canvas.app.run()
 '''


def view_patch_mplt(r,
                    attrib=[],
                    opacity=1,
                    fig=0,
                    show=1,
                    colorbar=1,
                    clim=[0],
                    outfile=0,
                    azimuth=0,
                    elevation=-90,
                    colormap='jet'):
    fig = plt.figure()
    fC = r.vColor[r.faces[:, 0], :]
    #    print fC.shape
    ax = fig.add_subplot(1, 1, 1, projection='3d', aspect='equal')
    LightSource(azdeg=0, altdeg=65)
    ax.view_init(azim=180, elev=0)
    ax.grid(False)
    t = ax.plot_trisurf(r.vertices[:, 0],
                        r.vertices[:, 1],
                        r.vertices[:, 2],
                        triangles=r.faces,
                        linewidth=0,
                        facecolors=fC,
                        antialiased=False)
    t.set_facecolors(fC)
    axisEqual3D(ax)
    ax.axis("off")
    #    plt.axis('equal')
    plt.show()


def view_patch(r,
               attrib=[],
               opacity=1,
               fig=0,
               show=1,
               colorbar=1,
               clim=[0],
               outfile=0,
               azimuth=0,
               elevation=-90,
               colormap='jet',
               close=1):

    if show == 0:
        mlab.options.offscreen = True
#    else:

    if fig == 0:
        fig = mlab.figure(bgcolor=(1, 1, 1),
                          fgcolor=(0.5, 0.5, 0.5))  #(bgcolor=(1,1,1))
    else:
        mlab.figure(fig)
    if len(attrib) > 0:
        if len(clim) > 1:
            vmin = clim[0]
            vmax = clim[1]
        else:
            vmax = sp.amax(attrib)
            vmin = sp.amin(attrib)
        mlab.triangular_mesh(r.vertices[:, 0],
                             r.vertices[:, 1],
                             r.vertices[:, 2],
                             r.faces,
                             representation='surface',
                             opacity=opacity,
                             scalars=attrib,
                             colormap=colormap,
                             vmin=vmin,
                             vmax=vmax)
    elif len(r.vColor) > 0:
        sc = sp.arange(r.vertices.shape[0])
        mt = mlab.triangular_mesh(r.vertices[:, 0],
                                  r.vertices[:, 1],
                                  r.vertices[:, 2],
                                  r.faces,
                                  representation='surface',
                                  scalars=sc)
        colors = 255 * sp.ones((r.vertices.shape[0], 4))
        colors[:, :3] = sp.int16(255.0 * r.vColor)
        mt.module_manager.scalar_lut_manager.lut.table = colors

    mlab.gcf().scene.parallel_projection = True
    mlab.view(azimuth=azimuth, elevation=elevation)

    if colorbar > 0:
        mlab.colorbar(orientation='horizontal')

    if show > 0:
        mlab.draw()
        mlab.show(stop=True)


#    else:
#    mlab.options.offscreen=True

    if outfile != 0:
        mlab.savefig(outfile)

    if close == 1:
        mlab.close()

    if show != 0:
        return fig


