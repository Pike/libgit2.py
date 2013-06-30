from collections import OrderedDict
import pdb
import sys
import os

from clang.cindex import Index, CursorKind, TypeKind


class Git2Processor(object):
    def __init__(self):
        self.structs = OrderedDict()
        self.data = OrderedDict()
        self.enums = OrderedDict()
    def parse(self, incpath):
        index = Index.create()
        tu = index.parse(None, [incpath])
        for diag in tu.diagnostics:
            if diag.location.file:
                fn = diag.location.file.name
            else:
                fn = "???"
            print >>sys.stderr, "Warning: %s:%d: %s" % (fn, diag.location.line, diag.spelling)
        self.tu = tu
    def process(self):
        currentfile = None
        files = 0
        for d in self.tu.cursor.get_children():
            if not d.location.file or 'git2' not in d.location.file.name:
                continue
            if currentfile != d.location.file.name:
                self.data['__files__' + str(files)] = {'kind': 'file', 'name': d.location.file.name}
                currentfile = d.location.file.name
                files += 1
            method = getattr(self, 'process_' + d.kind.name, self.process_Cursor)
            method(d)

    def process_Cursor(self, d):
        print 'unhandled', d.kind

    def process_FUNCTION_DECL(self, d):
        if d.type.kind != TypeKind.FUNCTIONPROTO:
            print >>sys.stderr, "XXX", "figure out non-proto functions", d.spelling, d.type.kind
            return
        args = list(d.get_arguments())
        ret = d.type.get_result()
        obj = {'kind': 'function',
               'result': self.resolvetype(ret, True),
               'args': [(arg.spelling, self.resolvetype(arg.type)) for arg in args]}
        self.data[d.spelling] = obj

    def process_STRUCT_DECL(self, d):
        # we don't need to do anything here, we'll find them in the typedef
        pass

    def process_ENUM_DECL(self, d):
        c = list(d.get_children())
        for enum_entry in c:
            self.data[enum_entry.spelling] = {'kind': 'enum',
                                              'value': enum_entry.enum_value}
    def process_TYPEDEF_DECL(self, d):
        c = list(d.get_children())
        if not c:
            print d.spelling, 'no children', d.type.get_canonical().kind
            return
        canonical = d.type.get_canonical()
        canonical_kind = canonical.kind

        if canonical_kind == TypeKind.ENUM:
            assert len(c) == 1
            entry = c[0]
            name = d.spelling
            obj = OrderedDict()
            for enum_entry in entry.get_children():
                obj[enum_entry.spelling] = enum_entry.enum_value
                self.data.pop(enum_entry.spelling)
            self.data[name] = {'kind': 'enum_type', 'values': obj}
        elif canonical_kind in (TypeKind.LONGLONG,):
            self.data[d.spelling] = {'kind': 'typedef',
                                     'realtype': self.resolvetype(canonical)}
        elif canonical_kind == TypeKind.RECORD:
            assert len(c) == 1
            entry = c[0]
            name = d.spelling
            fields = OrderedDict()
            for field_entry in entry.get_children():
                fields[field_entry.spelling] = self.resolvetype(field_entry.type)
            self.data[name] = {'kind': 'struct_type', 'fields': fields}
        elif (canonical_kind == TypeKind.POINTER and
              canonical.get_pointee().kind == TypeKind.FUNCTIONPROTO):
            self.data[d.spelling] = {'kind': 'callback',
                                     'CFUNCTYPE': self.resolvetype(canonical)}
        else:
            #pdb.set_trace()
            print 'unknown typedef entry kind', canonical_kind, d.spelling

    def resolvetype(self, t, is_pointer=False):
        if t.get_declaration().kind != CursorKind.NO_DECL_FOUND:
            t = t.get_declaration().type
    
        if t.kind == TypeKind.RECORD:
            return repr(t.get_declaration().spelling)
        if t.kind == TypeKind.ENUM:
            return repr(t.get_declaration().spelling)
        if t.kind == TypeKind.TYPEDEF:
            assert t.get_declaration().kind == CursorKind.TYPEDEF_DECL
    
            if t.get_declaration().spelling == "uint64_t":
                return "ctypes.c_uint64"
            elif t.get_declaration().spelling == "size_t":
                return "ctypes.c_size_t"
    
            # if the typedef is in specified file use the typedef name
            fname = t.get_declaration().location.file.name
            if 'git2' in fname:
                if is_pointer and not t.get_canonical().kind == TypeKind.ENUM:
                    # maybe "c_object_p"
                    return t.get_declaration().spelling
                else:
                    return repr(t.get_declaration().spelling)
    
            # otherwise use the canonical type
            return self.resolvetype(t.get_canonical())
        if t.kind == TypeKind.POINTER:
            pt = t.get_pointee()
            if pt.kind == TypeKind.CHAR_S:
                return "ctypes.c_char_p"
            if pt.kind == TypeKind.VOID:
                return "ctypes.c_void_p"
            if pt.kind in (TypeKind.UNEXPOSED, TypeKind.FUNCTIONPROTO):
                canon_t = pt.get_canonical()
                if canon_t.kind == TypeKind.FUNCTIONPROTO:
                    # anonymous callback function
                    return 'CFUNCTYPE(%s, %s)' % (
                        self.resolvetype(canon_t.get_result()),
                        ', '.join(self.resolvetype(at) for at in canon_t.argument_types())
                        )
            return "ctypes.POINTER(%s)" % self.resolvetype(pt, True)
        if t.kind == TypeKind.UINT:
            return "ctypes.c_uint"
        if t.kind == TypeKind.INT:
            return "ctypes.c_int"
        if t.kind == TypeKind.ULONGLONG:
            return "ctypes.c_ulonglong"
        if t.kind == TypeKind.LONGLONG:
            return "ctypes.c_longlong"
        if t.kind == TypeKind.ULONG:
            return "ctypes.c_ulong"
        if t.kind == TypeKind.LONG:
            return "ctypes.c_long"
        if t.kind == TypeKind.USHORT:
            return "ctypes.c_ushort"
        if t.kind == TypeKind.SHORT:
            return "ctypes.c_short"
        if t.kind == TypeKind.FLOAT:
            return "ctypes.c_float"
        if t.kind == TypeKind.DOUBLE:
            return "ctypes.c_double"
        if t.kind == TypeKind.VOID:
            return "None"
        if t.kind == TypeKind.CHAR_S:
            return "ctypes.c_char"
        if t.kind == TypeKind.UCHAR:
            return "ctypes.c_ubyte" ## Is uchar always same as ubyte?
        if t.kind == TypeKind.CONSTANTARRAY:
            return self.resolvetype(t.element_type) + ' * %d' % t.element_count
        if t.kind == TypeKind.UNEXPOSED:
            print >>sys.stderr, "XXX: how to find array args"
            pdb.set_trace()
            return "XXX: how to find array args"
        pdb.set_trace()
        return "UNKNOWN(%s)" % t.kind

if __name__ == '__main__':
    gp = Git2Processor()
    gp.parse(sys.argv[1])
    gp.process()
    for name, decl in gp.data.iteritems():
        print name, decl['kind']
