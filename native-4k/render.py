"""Original Avenzo 3D artwork. Blender 4.2.3 / Cycles. NO input photographs.
Every final pixel is rendered from geometry, analytic materials and lighting.
Run: blender -b -t 4 --python render.py -- --scene service-web --output renders
No original image is enlarged, traced, sampled or used as a texture.
"""
import bpy, math, random, sys, argparse, json, hashlib, struct, time
from pathlib import Path
from mathutils import Vector
PI=math.pi
STEMS=['hero-desktop-apps','hero-mobile-apps','service-web','service-ai','service-software','service-data','service-search','service-testing','software-closeup']
M={}

def mat(name,col,metal=0,rough=.35,emission=0,texture=None):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
    ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if emission:
        p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
    if texture:
        tc=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=38 if texture=='stone' else 170
        noise.inputs['Detail'].default_value=3
        if texture=='brushed':
            v=ns.new('ShaderNodeVectorMath');v.operation='MULTIPLY';v.inputs[1].default_value=(1,90,1);ls.new(tc.outputs['Generated'],v.inputs[0]);ls.new(v.outputs[0],noise.inputs['Vector'])
            p.inputs['Anisotropic IOR Level'].default_value=.42
        else: ls.new(tc.outputs['Generated'],noise.inputs['Vector'])
        bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13 if texture=='stone' else .08;bump.inputs['Distance'].default_value=.035 if texture=='stone' else .007
        ls.new(noise.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],p.inputs['Normal'])
        ramp=ns.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=max(.04,rough-.065);ramp.inputs['To Max'].default_value=rough+.08
        ls.new(noise.outputs['Fac'],ramp.inputs['Value']);ls.new(ramp.outputs['Result'],p.inputs['Roughness'])
    return m

def cube(name,loc,dim,material,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if material:o.data.materials.append(material)
    if bevel:
        mod=o.modifiers.new('Machined edge','BEVEL');mod.width=min(bevel,min(dim)*.42);mod.segments=4
        o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL')
    return o

def text(body,x,y,z,size=.1,material=None,align='LEFT'):
    c=bpy.data.curves.new('Vector typography','FONT');c.body=body;c.size=size;c.align_x=align;c.align_y='CENTER';c.resolution_u=8
    o=bpy.data.objects.new(body,c);bpy.context.collection.objects.link(o);o.location=(x,y,z);o.rotation_euler=(PI/2,0,0)
    c.materials.append(material or M['ink']);return o

def path(points,material,r=.012,name='Connection'):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=3;c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);c.materials.append(material);return o

def ring(x,y,z,r,thick,material,depth=None):
    if depth is None:
        bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=thick,major_segments=96,minor_segments=12,location=(x,y,z),rotation=(PI/2,0,0));o=bpy.context.object;o.data.materials.append(material)
        for p in o.data.polygons:p.use_smooth=True
        return o
    verts=[];faces=[];n=160
    for yy,rr in [(-depth/2,r),(-depth/2,r-thick),(depth/2,r),(depth/2,r-thick)]:
        verts += [(x+rr*math.cos(i*2*PI/n),y+yy,z+rr*math.sin(i*2*PI/n)) for i in range(n)]
    for a,b in [(0,1),(2,0),(1,3),(3,2)]:
        for i in range(n):j=(i+1)%n;faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
    me=bpy.data.meshes.new('Machined annulus');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Search ring',me);bpy.context.collection.objects.link(o);me.materials.append(material)
    bv=o.modifiers.new('Polished rim','BEVEL');bv.width=.025;bv.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def disk(x,y,z,r,material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=.004,location=(x,y,z),rotation=(PI/2,0,0));o=bpy.context.object;o.data.materials.append(material);return o

def area(name,loc,target,energy,size,color=(1,.94,.86)):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def camera(loc,target,ortho=None,lens=48):
    d=bpy.data.cameras.new('Camera');o=bpy.data.objects.new('Camera',d);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    bpy.context.scene.camera=o;return o

def materials():
    M.update(silver=mat('Brushed aluminium',(.55,.56,.55),1,.24,texture='brushed'),edge=mat('Polished edges',(.7,.71,.7),1,.15),red=mat('Bordeaux lacquer',(.16,.022,.038),.55,.24),ink=mat('Graphite',(.023,.026,.025),.15,.35),paper=mat('Display ivory',(.83,.82,.77),0,.42,.12),light=mat('Display white',(.93,.92,.88),0,.4,.12),muted=mat('Interface grey',(.43,.44,.41),0,.5),line=mat('Interface separators',(.61,.61,.57),0,.6),warm=mat('Warm light',(.95,.62,.3),0,.3,5),stone=mat('Limestone',(.43,.42,.39),0,.38,texture='stone'),dark=mat('Dark polished limestone',(.043,.047,.044),.16,.19,texture='stone'),wall=mat('Dark architectural concrete',(.058,.062,.057),0,.65,texture='stone'))

def plinth(x=0,y=0,w=4.8,d=1.5):
    cube('Rubber shadow gap',(x,y,.055),(w-.08,d-.05,.09),M['ink'],.028)
    cube('Brushed display plinth',(x,y,.18),(w,d,.22),M['silver'],.045)
    cube('Polished top edge',(x,y,.294),(w-.04,d-.04,.018),M['edge'],.01)

def pipes(x1,x2,y,z0,count=3,raise_y=0):
    for i in range(count):
        zz=z0+i*.20
        path([(x1,y,zz),(x1+.20,y,zz),(x1+.34,y+raise_y,zz),(x2-.20,y+raise_y,zz),(x2,y,zz)],M['red'],.033,'Bordeaux data connection')
        cube('Machined connector',(x1,y,zz),(.11,.16,.11),M['edge'],.018);cube('Machined connector',(x2,y,zz),(.11,.16,.11),M['edge'],.018)

def ui_line(x,y,z,w=.8):cube('Interface rule',(x+w/2,y,z),(w,.002,.012),M['line'],0)

def screen(x,y,z,w,h,kind='dashboard',phone=False):
    cube('Unibody display',(x,y,z),(w,.16,h),M['silver'],.065 if phone else .035)
    cube('Black glass rim',(x,y-.087,z),(w-.065,.034,h-.065),M['ink'],.055 if phone else .019)
    cube('Vector interface surface',(x,y-.108,z),(w-.13,.012,h-.13),M['paper'],.04 if phone else .008)
    for xx in (x-w/2+.043,x+w/2-.043):
        for zz in (z-h/2+.043,z+h/2-.043):disk(xx,y-.088,zz,.013,M['ink'])
    lx=x-w/2+.13;bz=z-h/2+.14;ww=w-.26;hh=h-.28;yy=y-.119
    def R(u,v,a,b,m):return cube('Interface vector',(lx+u*ww+a*ww/2,yy-.006,bz+v*hh+b*hh/2),(a*ww,.005,b*hh),m,0)
    def T(s,u,v,sz=.04,m=None):return text(s,lx+u*ww,yy-.014,bz+v*hh,sz*hh,m or M['ink'])
    R(-.018,.918,1.036,.096,M['red'])
    for i in range(3):disk(lx+(.018+i*.025)*ww,yy-.013,bz+.962*hh,hh*.007,M['paper'])
    T('avenzo',.84,.957,.024,M['paper'])
    if phone:
        cube('Camera island',(x,y-.127,z+h/2-.095),(w*.27,.013,.047),M['ink'],.02)
        T('AI Studio' if kind=='workflow' else ('Website' if kind=='web' else 'Projecten'),.04,.857,.063)
        R(.03,.76,.94,.035,M['light'])
        if kind=='workflow':
            nodes=[(.08,.65,'Invoer'),(.58,.65,'Data'),(.33,.47,'Analyse'),(.08,.27,'Review'),(.58,.27,'Actie')]
            for a,b,s in nodes:
                R(a,b,.32,.096,M['red']);T(s,a+.025,b+.045,.037,M['paper'])
            for a,b,c,d in [(.24,.65,.49,.57),(.74,.65,.49,.57),(.49,.47,.24,.37),(.49,.47,.74,.37)]:path([(lx+a*ww,yy-.01,bz+b*hh),(lx+a*ww,yy-.01,bz+d*hh),(lx+c*ww,yy-.01,bz+d*hh)],M['red'],.005)
        else:
            for i,s in enumerate(['Overzicht','Voortgang','Bestanden','Taken']):
                v=.60-i*.13;disk(lx+.1*ww,yy-.013,bz+v*hh,.025,M['red']);T(s,.21,v,.047);ui_line(lx+.21*ww,yy-.012,bz+(v-.038)*hh,.57*ww)
        R(.04,.055,.92,.09,M['red']);T('Open overzicht',.17,.096,.04,M['paper']);T('CONCEPT',.39,.008,.02,M['muted']);return
    R(.0,.05,.155,.845,M['light'])
    for i,s in enumerate(['Overzicht','Projecten','Bestanden','Taken','Instellingen']):T(s,.018,.84-i*.11,.022)
    for i in range(4):
        R(.024+i*.021,.035,.012,.024+i*.014,M['red'])
    if kind in ['config','web']:
        T('3D Configurator' if kind=='config' else 'Van visie.',.20,.854,.057)
        T('Naar voorsprong.' if kind=='web' else 'Ontwerp tot in detail',.20,.787,.031)
        # A vector-built architectural study, not an enlarged reference photograph.
        R(.20,.225,.61,.50,M['light']);R(.275,.325,.42,.255,M['muted']);R(.265,.57,.445,.035,M['red']);R(.278,.29,.47,.035,M['line'])
        for i in range(6):R(.299+i*.060,.335,.042,.224,M['ink']);R(.302+i*.060,.34,.012,.21,M['line'])
        R(.736,.34,.047,.23,M['red']);R(.235,.244,.54,.018,M['muted'])
        for i,c in enumerate([M['red'],M['muted'],M['ink'],M['silver'],M['stone'],M['line'],M['paper']]):R(.205+i*.081,.103,.063,.064,c)
        for i,s in enumerate(['Materiaal','Gevel','Afwerking','Kleur','Details']):T(s,.838,.71-i*.09,.024);ui_line(lx+.838*ww,yy-.008,bz+(.68-i*.09)*hh,.14*ww)
    elif kind=='workflow':
        T('AI Studio',.21,.855,.061)
        for i,s in enumerate(['Analyse','Verbind','Actie']):
            v=.64-i*.21;R(.22,v-.056,.67,.13,M['light']);disk(lx+.30*ww,yy-.014,bz+v*hh,hh*.029,M['red']);T(s,.40,v,.044)
            if i<2:path([(lx+.55*ww,yy-.014,bz+(v-.058)*hh),(lx+.55*ww,yy-.014,bz+(v-.15)*hh)],M['red'],.008)
    elif kind=='software':
        T('Projecten',.21,.855,.062)
        for i,s in enumerate(['Projecten','Bestanden','Taken']):
            v=.68-i*.20;R(.2,v-.09,.41,.15,M['light']);T(s,.245,v-.01,.038)
        R(.65,.12,.31,.66,M['ink']);T('</>',.70,.57,.14,M['paper']);T('const app = {',.69,.37,.031,M['line']);T('  project: ready',.69,.31,.025,M['line']);T('}',.69,.25,.032,M['line'])
    elif kind=='search':
        T('Zoeken',.22,.85,.060)
        for i,s in enumerate(['Websites & conversie','AI & automatisering','Software op maat']):
            v=.64-i*.23;R(.21,v-.08,.16,.15,M['red'] if i==0 else M['line']);T(s,.41,v+.025,.026)
            for j in range(3):ui_line(lx+.41*ww,yy-.011,bz+(v-.022-j*.038)*hh,(.46-j*.065)*ww)
    elif kind=='testing':
        T('Kwaliteitscontrole',.21,.85,.055)
        for i,s in enumerate(['Functies','Snelheid','Toegankelijkheid','Doorontwikkeling']):
            v=.69-i*.15;disk(lx+.255*ww,yy-.017,bz+v*hh,hh*.031,M['red']);path([(lx+.242*ww,yy-.023,bz+v*hh),(lx+.251*ww,yy-.023,bz+(v-.012)*hh),(lx+.270*ww,yy-.023,bz+(v+.014)*hh)],M['paper'],.006);T(s,.33,v,.04);ui_line(lx+.33*ww,yy-.01,bz+(v-.052)*hh,.54*ww)
    else:
        T('Dashboard',.21,.85,.06)
        for zz in [.63,.51,.39]:ui_line(lx+.21*ww,yy-.009,bz+zz*hh,.75*ww)
        vals=[.43,.49,.45,.58,.61,.55,.64,.62,.74]
        pts=[(lx+(.22+i*.087)*ww,yy-.016,bz+v*hh) for i,v in enumerate(vals)];path(pts,M['red'],.009)
        for xx,yyy,zz in pts:disk(xx,yyy-.005,zz,.018,M['red'])
        for i,v in enumerate([.10,.17,.21,.28,.22,.32]):R(.22+i*.045,.07,.029,v*.73,M['red'] if i%2 else M['line'])
        ring(lx+.64*ww,yy-.02,bz+.20*hh,.13*hh,.035*hh,M['line']);path([(lx+.64*ww+.13*hh*math.cos(t),yy-.024,bz+.20*hh+.13*hh*math.sin(t)) for t in [i*PI/80 for i in range(49)]],M['red'],.034*hh)
        for i,v in enumerate([.08,.11,.14,.20]):R(.80+i*.043,.07,.026,v,M['red'] if i%2 else M['line'])
    T('CONCEPTVISUALISATIE',.71,.012,.015,M['muted'])

def module(x,y,z,w=1.25,h=1.4,label='AI'):
    cube('Compute enclosure',(x,y,z),(w,1.10,h),M['silver'],.065)
    cube('Front machined face',(x,y-.56,z),(w-.09,.035,h-.08),M['edge'],.019)
    text(label,x,y-.585,z+.09,min(w*.30,.45),M['muted'],'CENTER')
    for j in range(7):cube('Vent slot',(x-w*.34+j*w*.115,y-.585,z-h*.33),(.026,.009,.09),M['ink'],.004)

def studio():
    cube('Studio limestone floor',(0,1,-.17),(200,200,.25),M['stone'],0)
    cube('Limestone wall',(0,5,5),(35,.25,12),M['stone'],0)
    for x in [-6,0,6]:cube('Panel joint',(x,4.866,5),(.015,.007,12),M['muted'],0)
    area('Large softbox',(-4,-4,8),(0,0,1),2300,7)
    area('Silver rim',(6,3,7),(0,0,1.5),2600,5,(.90,.94,1))
    area('Front fill',(1,-7,4),(0,0,1.5),650,6)
    camera((6,-12,6.0),(0,.2,1.55),ortho=9.8)

def tree(x,y,h=5):
    random.seed(round(x*77+y*21));bark=mat('Tree bark '+str(x),(.071,.052,.032),0,.9)
    leaves=mat('Olive foliage '+str(x),(.12,.14,.075),0,.69)
    path([(x,y,0),(x+.10,y,h*.42),(x-.10,y+.05,h*.75),(x+.05,y,h)],bark,.055)
    verts=[];faces=[]
    for k in range(16):
        a=k*2.4;zz=h*(.42+.029*k);rad=h*(.28-.010*k);end=Vector((x+math.cos(a)*rad,y+math.sin(a)*rad,zz+.50))
        path([(x,y,zz-.40),tuple(end*.5+Vector((x,y,zz))*.5),tuple(end)],bark,.018)
        for j in range(48):
            c=end+Vector((random.gauss(0,.36),random.gauss(0,.36),random.gauss(0,.29)))
            ang=random.random()*2*PI;v=Vector((math.cos(ang),math.sin(ang),random.uniform(-.5,.5)));u=Vector((-v.y,v.x,.25));l=random.uniform(.04,.095);i=len(verts)
            verts.extend([tuple(c-v*l),tuple(c+u*l*.34),tuple(c+v*l),tuple(c-u*l*.34)]);faces.append((i,i+1,i+2,i+3))
    me=bpy.data.meshes.new('Individual olive leaves');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Olive canopy',me);bpy.context.collection.objects.link(o);me.materials.append(leaves)

def ribbon():
    verts=[];faces=[];n=180
    for i in range(n+1):
        t=i/n;a=math.radians(-168+150*t);z=4.5+.8*t
        for r,dz in [(6.4,0),(7.25,0),(7.25,.63),(7.11,.63),(7.11,.10),(6.4,.10)]:verts.append((3.5+r*math.cos(a),7.5+r*math.sin(a),z+dz))
    for i in range(n):
        for j in range(6):faces.append((i*6+j,(i+1)*6+j,(i+1)*6+(j+1)%6,i*6+(j+1)%6))
    me=bpy.data.meshes.new('Curved architectural ramp');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Bordeaux ribbon',me);bpy.context.collection.objects.link(o);me.materials.append(M['red'])
    for p in me.polygons:p.use_smooth=True
    b=o.modifiers.new('Crafted edges','BEVEL');b.width=.025;b.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')

def atrium(mobile=False):
    cube('Polished atrium floor',(0,5,-.22),(60,65,.4),M['dark'],0)
    cube('Left monolithic wall',(-8,7,5),(20,.4,14),M['wall'],0)
    cube('Upper concrete slab',(0,6,8),(34,15,.5),M['wall'],.015)
    cube('Right structural wall',(13,6,5),(.5,20,13),M['wall'],.01)
    cube('Rear sill',(7,10,1),(17,.4,2),M['wall'],.01)
    for xx in range(-18,15,3):cube('Stone floor joint',(xx,2,-.010),(.009,55,.006),M['ink'],0)
    for yy in range(-15,20,3):cube('Stone floor joint',(0,yy,-.010),(55,.009,.006),M['ink'],0)
    for xx in range(1,14):cube('Window mullion',(xx,10,5),(.048,.06,7),M['ink'],.005)
    for xx in [-10,-7,-4,-1,2,5,8,11]:
        cube('Floor light',(xx,6.65,.08),(.045,.09,.18),M['warm'],.01);area('Wall wash '+str(xx),(xx,6.2,.25),(xx,7,1.8),35,.23,(1,.67,.38))
    ribbon();tree(.8,5.7,5.3);tree(10,6,6)
    area('Daylight clerestory',(9,6,10),(2,0,1.8),5400,8,(.9,.94,1))
    area('Architectural key',(-1,-2,7),(4,0,1.5),1900,6,(1,.86,.71))
    area('Device edge light',(9,1,6),(4,0,1.8),2000,4)
    area('Display fill',(1,-7,5),(4,0,2),850,6)
    plinth(3.1,-.15,5.2,1.75);screen(3.1,.1,2.00,4.5,3.14,'config')
    module(6.1,.35,1.1,1.35,1.62,'AI');pipes(5.35,6.03,.08,.80)
    plinth(5.25,-1.45,1.90,1.25);screen(5.25,-1.46,1.65,1.25,2.63,'workflow',True)
    cube('Rear interface plate',(4.9,1,2.2),(2.6,.20,3.75),M['silver'],.035)
    if mobile:camera((4.8,-12.8,5.6),(3.8,1.0,3.0),lens=42)
    else:camera((0,-19,5.5),(0,1.0,2.65),lens=36)

def scene_geometry(name):
    if name.startswith('hero-'):atrium(name=='hero-mobile-apps');return
    studio()
    if name=='service-web':
        plinth(-.35,.1,5,1.65);screen(-.35,.35,2.12,4.55,3.50,'web');cube('Rear service plate',(1.55,1.02,1.95),(1.6,.16,3.20),M['silver'],.03)
        plinth(2.18,-1,1.7,1.2);screen(2.18,-1,1.64,1.21,2.64,'web',True);pipes(.95,2.58,.84,.79)
    elif name=='service-ai':
        plinth(-2,0,3,2.05);module(-2,.10,1.24,2.42,1.76,'AI');plinth(2.12,0,2.90,1.5);screen(2.12,.1,1.94,2.60,3.12,'workflow');pipes(-.76,.78,-.1,.84)
    elif name=='service-software':
        plinth(0,.25,6.8,3.0);screen(.2,1.15,2.5,4.7,3.9,'dashboard');screen(-.8,-.45,1.65,4.45,2.65,'software');module(2.45,-.15,1.13,1.40,1.66,'</>');pipes(1.45,2.46,.20,.82)
    elif name=='service-data':
        plinth(-.2,.2,5.35,1.85);screen(-.3,.20,2.17,4.70,3.58,'dashboard');cube('Rear modular panel',(-2.45,.75,2.11),(.42,.35,3.52),M['silver'],.045)
        plinth(2,-1.12,2.5,1.14)
        for i,h in enumerate([.65,1.1,1.58,2.13]):cube('Physical data column',(1.2+i*.50,-1.13,.31+h/2),(.34,.64,h),M['red'] if i%2 else M['silver'],.021)
    elif name=='service-search':
        ring(-1.85,.0,1.98,1.62,.30,M['silver'],.58);plinth(-1.85,0,3.0,1.25)
        cube('Search field',(-1.8,-.63,1.9),(3.60,.18,.64),M['silver'],.055);cube('Search surface',(-1.8,-.73,1.9),(3.44,.019,.50),M['paper'],.025)
        ring(-3.06,-.75,1.96,.105,.016,M['ink']);path([(-2.99,-.75,1.885),(-2.91,-.75,1.80)],M['ink'],.018);text('Zoeken',-2.63,-.753,1.91,.20,M['muted'])
        screen(2.50,1.05,2.04,2.48,3.2,'search');screen(1.80,.15,1.84,2.46,3.13,'search');pipes(-.13,.65,.80,.85)
    elif name=='service-testing':
        plinth(-.4,.1,5.4,1.8);screen(-.45,.15,2.13,4.6,3.5,'testing');module(2.45,.50,1.3,1.45,1.90,'</>');pipes(1.68,2.46,.53,.73)
        plinth(2.03,-1.25,1.7,1.16);screen(2.03,-1.25,1.63,1.18,2.64,'testing',True)
    elif name=='software-closeup':
        plinth(0,.4,7.8,4.6);screen(-.6,-1.2,2.16,5.45,3.7,'software');module(1.13,1.20,1.90,1.95,2.7,'AI');module(3.30,1.3,1.80,1.4,2.5,'</>')
        cube('Rear silver layer',(-1.2,2.2,2.2),(5.6,.19,4.0),M['silver'],.045);cube('Middle silver layer',(-1,1.6,2.2),(5.6,.16,3.8),M['silver'],.045);pipes(-.9,2.28,.54,1.45,4,.45)
        camera((5.9,-6.1,7.1),(.10,.1,1.7),ortho=8.2)

def main():
    p=argparse.ArgumentParser();p.add_argument('--scene',choices=STEMS,required=True);p.add_argument('--output',default='renders');p.add_argument('--width',type=int,default=3840);p.add_argument('--samples',type=int,default=64);args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    if args.width<320:raise ValueError('Render width too small')
    start=time.time();bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=args.samples;s.cycles.use_denoising=True;s.cycles.adaptive_threshold=.025;s.cycles.max_bounces=7;s.cycles.diffuse_bounces=3;s.cycles.glossy_bounces=4;s.cycles.sample_clamp_indirect=4;s.render.threads_mode='FIXED';s.render.threads=4
    world=bpy.data.worlds.new('Studio environment');s.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.50,.51,.51,1);world.node_tree.nodes['Background'].inputs[1].default_value=.22 if args.scene.startswith('hero') else .35
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.40
    materials();scene_geometry(args.scene)
    ratio=1106/1422 if args.scene=='hero-mobile-apps' else (1586/992 if args.scene.startswith('service-') else 16/9)
    w=args.width;h=round(w/ratio);s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=35
    # Never use a compositor scaler, AI super-resolution, texture photograph or resize.
    s.use_nodes=False
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True);image=out/(args.scene+'.png');s.render.filepath=str(image)
    report={'scene':args.scene,'engine':'Blender '+bpy.app.version_string+' / Cycles CPU','native_render_width':w,'native_render_height':h,'resolution_percentage':100,'samples_max':args.samples,'input_raster_textures':len([i for i in bpy.data.images if i.source=='FILE']),'upscaling':False,'source_kind':'Original procedural 3D geometry, vector typography, analytic shaders and lighting','objects':len(bpy.data.objects),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'deployment_performed':False}
    if report['input_raster_textures']:raise RuntimeError('Raster texture found; this renderer must be entirely original geometry')
    bpy.ops.render.render(write_still=True)
    with image.open('rb') as f:head=f.read(24)
    rw,rh=struct.unpack('>II',head[16:24]);assert (rw,rh)==(w,h)
    report.update(output_sha256=hashlib.sha256(image.read_bytes()).hexdigest(),seconds=round(time.time()-start,2),output_bytes=image.stat().st_size)
    (out/(args.scene+'.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
