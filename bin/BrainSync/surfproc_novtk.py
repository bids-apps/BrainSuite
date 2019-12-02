'''||AUM||'''
import numpy as np
from scipy.sparse.linalg import cg  # ,spilu,LinearOperator
from scipy.sparse import eye, spdiags, csc_matrix, vstack
from dfsio import readdfs
import scipy as sp

__author__ = "Anand A. Joshi"
__copyright__ = "University of Southern California, Los Angeles"
__email__ = "ajoshi@sipi.usc.edu"

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
    v2_v1temp = V2-V1
    x2 = np.linalg.norm(v2_v1temp, axis=1)
    y2 = np.zeros((NumTri))
    x3 = np.einsum('ij,ij->i', (V3-V1),
                   (v2_v1temp/np.column_stack((x2, x2, x2))))
    mynorm = np.cross((v2_v1temp), V3-V1, axis=1)
    yunit = np.cross(mynorm, v2_v1temp, axis=1)
    y3 = np.einsum('ij,ij->i', yunit, (V3-V1))/np.linalg.norm(yunit, axis=1)
    sqrt_DT = (np.abs((x1*y2 - y1*x2)+(x2*y3 - y2*x3)+(x3*y1 - y3*x1)))
    Ar = 0.5*(np.abs((x1*y2 - y1*x2)+(x2*y3 - y2*x3)+(x3*y1 - y3*x1)))

    TC = face_v_conn(surf1)
    Wt = (1.0/3.0)*(TC)
    # Wt = sp.sparse.spdiags(Wt*Ar, (0), NumTri, NumTri)
    surf_weight = sp.sqrt(Wt*Ar)
    return surf_weight


def patch_color_labels(s,freq=[1],cmap='Paired', shuffle=True):
    ''' color by freq of labels '''
    s.vColor = sp.zeros(s.vertices.shape)
    _, labels = sp.unique(s.labels, return_inverse=True)
    labels += 1
    colr = get_cmap(sp.amax(labels)+1,cmap=cmap)
    s.vColor = s.vColor+1
    perm1=sp.mod(3511*sp.arange(sp.amax(labels)+1),sp.amax(labels)+1)
    freq=sp.reshape(freq,(len(freq),1))
    if shuffle==True:
        s.vColor = (1-freq) + freq*sp.array(colr(perm1[labels])[:,:3])
    else:
        s.vColor = (1-freq) + freq*sp.array(colr(labels)[:,:3])
    return s

def patch_color_attrib(s,values=[],cmap='jet', clim=[0]):
    ''' color by freq of labels '''
    if len(values) == 0:
        values = s.attributes
    if len(clim) == 1:
        vmin = sp.amin(values); vmax = sp.amax(values)
    else:
        vmin = clim[0]; vmax = clim[1]


    s.vColor = sp.zeros(s.vertices.shape)
    color_norm  = colors.Normalize(vmin=vmin,vmax=vmax)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=cmap)
    s.vColor = scalar_map.to_rgba(values)
    s.vColor =  s.vColor[:,:3]
    return s


def get_cmap(N,cmap='jet'):
    '''Returns a function that maps each index in 0, 1, ... N-1 to a distinct
    RGB color.'''
    color_norm  = colors.Normalize(vmin=0, vmax=N-1)
    scalar_map = cmx.ScalarMappable(norm=color_norm, cmap=cmap)
    def map_index_to_rgb_color(index):
        return scalar_map.to_rgba(index)
    return map_index_to_rgb_color


def face_areas(s):
    r12 = s.vertices[s.faces[:, 0],:]
    r13 = s.vertices[s.faces[:, 2],:] - r12
    r12 = s.vertices[s.faces[:, 1],:] - r12
    area1 = sp.sqrt(sp.sum(sp.cross(r12,r13)** 2, axis=1)) / 2.0
    return area1


def smooth_surf_function(s, f0, a1=3.1, a2=3.1, aniso=None, normalize=0):

    if aniso is None:
        aniso = np.ones((len(s.vertices), 1))

    S, Dx, Dy = get_stiffness_matrix_tri_wt(s, aniso)
    M = vstack((a1*S, a2*vstack((Dx, Dy))))
    A = vstack((eye(len(s.vertices)), M))
    b = np.concatenate((f0, np.zeros(M.shape[0])))
    AtA = A.T*A

    M = spdiags(1.0/AtA.diagonal(), [0], AtA.shape[0], AtA.shape[1])
#    M=np.diag(np.diag(A.transpose()*A))
    f, nits = cg(AtA, A.T*b, tol=1e-100, maxiter=600, M=M)
#    print('f',f)
    if normalize > 0:
        f = f*np.linalg.norm(f0)/np.linalg.norm(f)

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
    v2_v1temp = V2-V1
    x2 = np.linalg.norm(v2_v1temp, axis=1)
    y2 = np.zeros((NumTri))
    x3 = np.einsum('ij,ij->i', (V3-V1),
                   (v2_v1temp/np.column_stack((x2, x2, x2))))
    mynorm = np.cross((v2_v1temp), V3-V1, axis=1)
    yunit = np.cross(mynorm, v2_v1temp, axis=1)
    y3 = np.einsum('ij,ij->i', yunit, (V3-V1))/np.linalg.norm(yunit, axis=1)
    sqrt_DT = (np.abs((x1*y2 - y1*x2)+(x2*y3 - y2*x3)+(x3*y1 - y3*x1)))
    Ar = 0.5*(np.abs((x1*y2 - y1*x2)+(x2*y3 - y2*x3)+(x3*y1 - y3*x1)))
#    Ar=1.0+0.0*Ar
    y1 = y1/sqrt_DT
    y2 = y2/sqrt_DT
    y3 = y3/sqrt_DT
    x1 = x1/sqrt_DT
    x2 = x2/sqrt_DT
    x3 = x3/sqrt_DT
    tmp_A = np.concatenate((y2-y3, y3-y1, y1-y2), axis=0)
    tmp_B = np.concatenate((x3-x2, x1-x3, x2-x1), axis=0)

    rowno = np.arange(0, NumTri)
    rowno_all = np.concatenate((rowno, rowno, rowno))
    vertx_all = np.concatenate((vertx_1, vertx_2, vertx_3))
    Dx = csc_matrix((tmp_A, (rowno_all, vertx_all)), (NumTri, len(X)))
    Dy = csc_matrix((tmp_B, (rowno_all, vertx_all)), (NumTri, len(X)))

    TC = face_v_conn(surf1)
    Wt = (1.0/3.0)*(TC.T*W)
    Wt = spdiags(Wt*Ar, (0), NumTri, NumTri)
    S = Dx.T*Wt*Dx + Dy.T*Wt*Dy

    return S, Dx, Dy


def face_v_conn(FV):

    nFaces = FV.faces.shape[0]
#    nVertices = FV.vertices.shape[0]

    rows = np.concatenate((FV.faces[:, 0], FV.faces[:, 1], FV.faces[:, 2]))
    cols = np.concatenate((np.arange(0, nFaces), np.arange(0, nFaces),
                           np.arange(0, nFaces)))
    data = np.ones((len(rows)))
    TriConn = csc_matrix((data, (rows, cols)))

    return TriConn

def axisEqual3D(ax):
    extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
    sz = extents[:,1] - extents[:,0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize/2
    for ctr, dim in zip(centers, 'xyz'):
        getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)


from mpl_toolkits.mplot3d import Axes3D
import matplotlib.tri as mtri
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
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

def view_patch_mplt(r, attrib=[], opacity=1, fig=0, show=1, colorbar=1, clim=[0], outfile=0, azimuth=0, elevation=-90, colormap='jet'):
    fig = plt.figure()
    fC=r.vColor[r.faces[:,0],:]
#    print fC.shape
    ax = fig.add_subplot(1, 1, 1, projection='3d',aspect='equal')
    LightSource(azdeg=0, altdeg=65)
    ax.view_init(azim=180, elev=0)
    ax.grid(False)
    t = ax.plot_trisurf(r.vertices[:,0], r.vertices[:,1], r.vertices[:,2],
                    triangles=r.faces, linewidth=0, facecolors=fC, antialiased=False)
    t.set_facecolors(fC)
    axisEqual3D(ax)
    ax.axis("off")
#    plt.axis('equal')
    plt.show()




def view_patch(r, attrib=[], opacity=1, fig=0, show=1, colorbar=1, clim=[0], outfile=0, azimuth=0, elevation=-90, colormap='jet', close=1):

    if show == 0:
        mlab.options.offscreen=True
#    else:

    if fig == 0:
        fig = mlab.figure(bgcolor=(1, 1, 1), fgcolor=(0.5, 0.5, 0.5)) #(bgcolor=(1,1,1))
    else:
        mlab.figure(fig)
    if len(attrib) > 0:
        if len(clim)>1:
            vmin=clim[0];vmax=clim[1]
        else:
            vmax=sp.amax(attrib);vmin=sp.amin(attrib)
        mlab.triangular_mesh(r.vertices[:, 0], r.vertices[:, 1],
                             r.vertices[:, 2], r.faces,
                             representation='surface', opacity=opacity,
                             scalars=attrib, colormap=colormap, vmin=vmin,
                             vmax=vmax)
    elif len(r.vColor)>0 :
        sc=sp.arange(r.vertices.shape[0])
        mt=mlab.triangular_mesh(r.vertices[:, 0], r.vertices[:, 1],
                             r.vertices[:, 2],
                             r.faces, representation='surface',
                             scalars=sc)
        colors=255*sp.ones((r.vertices.shape[0],4))
        colors[:,:3]=sp.int16(255.0*r.vColor)
        mt.module_manager.scalar_lut_manager.lut.table = colors

    mlab.gcf().scene.parallel_projection = True
    mlab.view(azimuth=azimuth, elevation=elevation)

    if colorbar>0:
        mlab.colorbar(orientation='horizontal')

    if show > 0:
        mlab.draw()
        mlab.show(stop=True)

#    else:
#    mlab.options.offscreen=True

    if outfile != 0:
        mlab.savefig(outfile)

    if close==1:
        mlab.close()


    if show != 0:
        return fig

