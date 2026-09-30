import ctypes as C
r=C.CDLL('librsvg-2.so.2');c=C.CDLL('libcairo.so.2');g=C.CDLL('libgobject-2.0.so.0')
r.rsvg_handle_new_from_file.argtypes=[C.c_char_p,C.c_void_p];r.rsvg_handle_new_from_file.restype=C.c_void_p
r.rsvg_handle_render_cairo.argtypes=[C.c_void_p,C.c_void_p];r.rsvg_handle_render_cairo.restype=C.c_int
c.cairo_image_surface_create.argtypes=[C.c_int,C.c_int,C.c_int];c.cairo_image_surface_create.restype=C.c_void_p
c.cairo_create.argtypes=[C.c_void_p];c.cairo_create.restype=C.c_void_p
c.cairo_scale.argtypes=[C.c_void_p,C.c_double,C.c_double];c.cairo_surface_write_to_png.argtypes=[C.c_void_p,C.c_char_p]
h=r.rsvg_handle_new_from_file(b'work/four_compare/comparison.svg',None);assert h
s=c.cairo_image_surface_create(0,1760,960);ctx=c.cairo_create(s);c.cairo_scale(ctx,2,2);assert r.rsvg_handle_render_cairo(h,ctx);assert c.cairo_surface_write_to_png(s,b'work/four_compare/comparison.png')==0
print('SVG rendered successfully with librsvg')
