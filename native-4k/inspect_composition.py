"""Geometry-only framing audit. No rendering, image resizing or deployment."""
import bpy, json, sys, importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=Path(__file__).with_name('render.py');spec=importlib.util.spec_from_file_location('avenzo_renderer',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report=[]
for stem in m.STEMS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    ratio=1106/1422 if stem=='hero-mobile-apps' else (1586/992 if stem.startswith('service-') else 16/9)
    scene.render.resolution_x=3840;scene.render.resolution_y=round(3840/ratio);scene.render.resolution_percentage=100
    m.materials();m.scene_geometry(stem);bpy.context.view_layer.update()
    objects=[]
    for obj in bpy.data.objects:
        if not obj.name.startswith(('Unibody display','Compute enclosure','Search ring')):continue
        points=[world_to_camera_view(scene,scene.camera,obj.matrix_world@Vector(corner)) for corner in obj.bound_box]
        bounds=[min(p.x for p in points),1-max(p.y for p in points),max(p.x for p in points),1-min(p.y for p in points)]
        objects.append({'name':obj.name,'image_bounds_fraction':[round(v,4) for v in bounds],'fully_in_native_frame':all(v>=0 for v in bounds[:2]) and all(v<=1 for v in bounds[2:])})
    report.append({'scene':stem,'objects':objects})
print('AVENZO_COMPOSITION_REPORT_START')
print(json.dumps(report,indent=2))
print('AVENZO_COMPOSITION_REPORT_END')
out=Path('composition');out.mkdir(exist_ok=True);(out/'framing.json').write_text(json.dumps(report,indent=2))
