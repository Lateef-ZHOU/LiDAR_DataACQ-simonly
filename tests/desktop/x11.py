"""Bounded X11 inspection/WM_DELETE_WINDOW for our isolated desktop tests (Linux only)."""
import ctypes as c
import struct
import zlib
from pathlib import Path

class Attributes(c.Structure):
    _fields_ = [(x, c.c_int) for x in ('x','y','width','height','border_width','depth')] + [
        ('visual', c.c_void_p), ('root', c.c_ulong)] + [
        (x, c.c_int) for x in ('klass','bit_gravity','win_gravity','backing_store')] + [
        ('backing_planes', c.c_ulong), ('backing_pixel', c.c_ulong), ('save_under', c.c_int),
        ('colormap', c.c_ulong), ('map_installed', c.c_int), ('map_state', c.c_int),
        ('all_event_masks', c.c_long), ('your_event_mask', c.c_long), ('do_not_propagate_mask', c.c_long),
        ('override_redirect', c.c_int), ('screen', c.c_void_p)]

class Image(c.Structure):
    _fields_ = [(x,c.c_int) for x in ('width','height','xoffset','format')] + [('data',c.c_void_p)] + [
        (x,c.c_int) for x in ('byte_order','bitmap_unit','bitmap_bit_order','bitmap_pad','depth','bytes_per_line','bits_per_pixel')] + [
        (x,c.c_ulong) for x in ('red_mask','green_mask','blue_mask')]

class Data(c.Union):
    _fields_ = [('b', c.c_char*20), ('s',c.c_short*10), ('l',c.c_long*5)]

class Client(c.Structure):
    _fields_ = [('type',c.c_int), ('serial',c.c_ulong), ('send_event',c.c_int), ('display',c.c_void_p),
                ('window',c.c_ulong), ('message_type',c.c_ulong), ('format',c.c_int), ('data',Data)]

class Event(c.Union):
    _fields_ = [('client',Client), ('pad',c.c_long*24)]

class Desktop:
    def __init__(self):
        self.lib = c.CDLL('libX11.so.6')
        signatures = {
            'XOpenDisplay': (c.c_void_p,[c.c_char_p]),
            'XDefaultRootWindow': (c.c_ulong,[c.c_void_p]),
            'XQueryTree': (c.c_int,[c.c_void_p,c.c_ulong,c.POINTER(c.c_ulong),c.POINTER(c.c_ulong),
                                  c.POINTER(c.POINTER(c.c_ulong)),c.POINTER(c.c_uint)]),
            'XGetWindowAttributes': (c.c_int,[c.c_void_p,c.c_ulong,c.POINTER(Attributes)]),
            'XGetWindowProperty': (c.c_int,[c.c_void_p,c.c_ulong,c.c_ulong,c.c_long,c.c_long,c.c_int,c.c_ulong,
                c.POINTER(c.c_ulong),c.POINTER(c.c_int),c.POINTER(c.c_ulong),c.POINTER(c.c_ulong),c.POINTER(c.c_void_p)]),
            'XFree': (c.c_int,[c.c_void_p]),
            'XInternAtom': (c.c_ulong,[c.c_void_p,c.c_char_p,c.c_int]),
            'XSendEvent': (c.c_int,[c.c_void_p,c.c_ulong,c.c_int,c.c_long,c.POINTER(Event)]),
            'XFlush': (c.c_int,[c.c_void_p]),
            'XGetImage': (c.POINTER(Image),[c.c_void_p,c.c_ulong,c.c_int,c.c_int,c.c_uint,c.c_uint,c.c_ulong,c.c_int]),
            'XDestroyImage': (c.c_int,[c.c_void_p]),
        }
        for name,(result,args) in signatures.items():
            fn=getattr(self.lib,name); fn.restype=result; fn.argtypes=args
        self.display=self.lib.XOpenDisplay(None)
        if not self.display: raise RuntimeError('Cannot connect to authenticated test DISPLAY')

    def window(self):
        def walk(parent, depth):
            root=c.c_ulong(); owner=c.c_ulong(); count=c.c_uint(); children=c.POINTER(c.c_ulong)()
            if not self.lib.XQueryTree(self.display,parent,c.byref(root),c.byref(owner),c.byref(children),c.byref(count)):
                return None
            ids=list(children[:count.value]); self.lib.XFree(children)
            for win in ids:
                attrs=Attributes(); title=c.c_void_p()
                if not self.lib.XGetWindowAttributes(self.display,win,c.byref(attrs)): continue
                name=b''
                actual=c.c_ulong(); fmt=c.c_int(); size=c.c_ulong(); after=c.c_ulong()
                prop=self.lib.XInternAtom(self.display,b'_NET_WM_NAME',0)
                if self.lib.XGetWindowProperty(self.display,win,prop,0,1024,0,0,c.byref(actual),c.byref(fmt),
                                               c.byref(size),c.byref(after),c.byref(title))==0 and title:
                    if fmt.value==8: name=c.string_at(title,size.value)
                    self.lib.XFree(title)
                if name.startswith(b'LiDAR') and attrs.map_state==2 and attrs.width>500:
                    return win,attrs
                if depth and attrs.map_state==2:
                    nested=walk(win,depth-1)
                    if nested: return nested
            return None
        return walk(self.lib.XDefaultRootWindow(self.display),2)

    def close(self, win):
        event=Event()
        event.client.type=33 # ClientMessage / WM_PROTOCOLS
        event.client.display=self.display; event.client.window=win
        event.client.message_type=self.lib.XInternAtom(self.display,b'WM_PROTOCOLS',0)
        event.client.format=32
        event.client.data.l[0]=self.lib.XInternAtom(self.display,b'WM_DELETE_WINDOW',0)
        self.lib.XSendEvent(self.display,win,0,0,c.byref(event))
        self.lib.XFlush(self.display)

    def capture(self, win, attrs, filename):
        ptr=self.lib.XGetImage(self.display,win,0,0,attrs.width,attrs.height,c.c_ulong(-1).value,2)
        if not ptr: raise RuntimeError('XGetImage failed')
        image=ptr.contents
        try:
            if image.bits_per_pixel!=32 or image.byte_order!=0 or (image.red_mask,image.green_mask,image.blue_mask)!=(0xff0000,0xff00,0xff):
                raise RuntimeError('Test capture expects little-endian 32-bit RGB storage')
            data=c.string_at(image.data,image.bytes_per_line*image.height)
            rows=[]; colors=set(); colored=0
            for y in range(image.height):
                raw=data[y*image.bytes_per_line:y*image.bytes_per_line+image.width*4]
                rgb=bytearray(image.width*3); rgb[0::3]=raw[2::4]; rgb[1::3]=raw[1::4]; rgb[2::3]=raw[0::4]
                rows.append(b'\0'+rgb)
                if 160<y<image.height-50:
                    for x in range(30,max(30,image.width-440),2):
                        r,g,b=rgb[x*3:x*3+3]
                        if max(r,g,b)-min(r,g,b)>45 and min(r,g,b)>15:
                            colors.add((r//4,g//4,b//4)); colored+=1
            def chunk(kind, payload):
                return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
            png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',image.width,image.height,8,2,0,0,0))
            png+=chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
            Path(filename).write_bytes(png)
            return {'width':image.width,'height':image.height,'plot_colors':len(colors),'plot_colored_samples':colored}
        finally:
            self.lib.XDestroyImage(ptr)
