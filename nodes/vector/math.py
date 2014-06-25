# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import EnumProperty
from mathutils import noise, Vector

from node_tree import SverchCustomTreeNode, VerticesSocket
from data_structure import (fullList, levelsOflist, updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)


class VectorMathNode(bpy.types.Node, SverchCustomTreeNode):
    ''' VectorMathNode '''
    bl_idname = 'VectorMathNode'
    bl_label = 'Vector Math'
    bl_icon = 'OUTLINER_OB_EMPTY'

    # vector math functions
    # normalize, length
    mode_items = [
        ("CROSS",       "Cross product",        "", 0),
        ("DOT",         "Dot product",          "", 1),
        ("ADD",         "Add",                  "", 2),
        ("SUB",         "Sub",                  "", 3),
        ("LEN",         "Length",               "", 4),
        ("DISTANCE",    "Distance",             "", 5),
        ("NORMALIZE",   "Normalize",            "", 6),
        ("NEG",         "Negate",               "", 7),
        ("NOISE-V",     "Noise Vector",         "", 8),
        ("NOISE-S",     "Noise Scalar",         "", 9),
        ("CELL-V",      "Vector Cell noise",    "", 10),
        ("CELL-S",      "Scalar Cell noise",    "", 11),
        ("ANGLE",       "Angle",                "", 12),
        ("PROJECT",     "Project",              "", 13),
        ("REFLECT",     "Reflect",              "", 14),
        ]

    items_ = EnumProperty(name="Function", description="Function choice",
                          default="CROSS", items=mode_items,
                          update=updateNode)
    # matches default of CROSS product
    scalar_output_socket = False

    def draw_buttons(self, context, layout):
        layout.prop(self, "items_", "Functions:")

    def init(self, context):
        self.inputs.new('VerticesSocket', "U", "u")
        self.inputs.new('VerticesSocket', "V", "v")
        self.outputs.new('VerticesSocket', "W", "W")

    def update(self):

        scalar_out = {
            "DOT"       :   (lambda u, v: u.dot(v), 2),
            "DISTANCE"  :   (lambda u, v: (u-v).length, 2),
            "LEN"       :   (lambda u   : u.length, 1),
            "NOISE-S"   :   (lambda u   : noise.noise(u), 1),
            "CELL-S"    :   (lambda u   : noise.cell(u), 1),
            "ANGLE"     :   (lambda u, v: u.angle(v, 0), 2),
        }

        vector_out = {
            "CROSS"     :   (lambda u, v: u.cross(v), 2),
            "ADD"       :   (lambda u, v: u + v, 2),
            "SUB"       :   (lambda u, v: u - v, 2),
            "NORMALIZE" :   (lambda u   : u.normalized(), 1),
            "NEG"       :   (lambda u   : -u, 1),
            "NOISE-V"   :   (lambda u   : noise.noise_vector(u), 1),
            "CELL-V"    :   (lambda u   : noise.cell_vector(u), 1),
            "REFLECT"   :   (lambda u, v: u.reflect(v), 2),
            "PROJECT"   :   (lambda u, v: u.project(v), 2),
        }

        # check and adjust outputs and input size

        if self.items_ in scalar_out:
            nrInputs = scalar_out[self.items_][1]
            if 'W' in self.outputs:
                self.outputs.remove(self.outputs['W'])
                self.outputs.new('StringsSocket', "out", "out")
            self.scalar_output_socket = True

        elif self.items_ in vector_out:
            nrInputs = vector_out[self.items_][1]
            if 'out' in self.outputs:
                self.outputs.remove(self.outputs['out'])
                self.outputs.new('VerticesSocket', "W", "W")
            self.scalar_output_socket = False

        # adjust inputs

        if nrInputs < len(self.inputs):
            self.inputs.remove(self.inputs['V'])
        elif nrInputs > len(self.inputs):
            self.inputs.new('VerticesSocket', "V", "v")

        self.label = self.items_

        # get inputs

        # vector-output
        if 'W' in self.outputs and self.outputs['W'].links:

            if 'U' in self.inputs and self.inputs['U'].links and \
               type(self.inputs['U'].links[0].from_socket) == VerticesSocket:
                vector1 = SvGetSocketAnyType(self, self.inputs['U'])
            else:
                vector1 = []

            if 'V' in self.inputs and self.inputs['V'].links and \
               type(self.inputs['V'].links[0].from_socket) == VerticesSocket:
                vector2 = SvGetSocketAnyType(self, self.inputs['V'])
            else:
                vector2 = []

            result = []

            if nrInputs == 1:
                if len(vector1):
                    u = vector1
                    leve = levelsOflist(u)
                    try:
                        result = self.recurse_fx(u, vector_out[self.items_][0], leve-1)
                    except:
                        print(self.name)
            if nrInputs == 2:
                if len(vector1) and len(vector2):
                    u = vector1
                    v = vector2
                    leve = levelsOflist(u)
                    try:
                        result = self.recurse_fxy(u, v, vector_out[self.items_][0], leve-1)
                    except:
                        print(self.name)
            SvSetSocketAnyType(self, 'W', result)

        # scalar-output
        if 'out' in self.outputs and self.outputs['out'].links:

            if 'U' in self.inputs and self.inputs['U'].links and \
               type(self.inputs['U'].links[0].from_socket) == VerticesSocket:
                vector1 = SvGetSocketAnyType(self, self.inputs['U'])
            else:
                vector1 = []

            if 'V' in self.inputs and self.inputs['V'].links and \
               type(self.inputs['V'].links[0].from_socket) == VerticesSocket:
                vector2 = SvGetSocketAnyType(self, self.inputs['V'])
            else:
                vector2 = []

            result = []
            if nrInputs == 1:
                if len(vector1):
                    u = vector1
                    leve = levelsOflist(u)
                    try:
                        result = self.recurse_fx(u, scalar_out[self.items_][0], leve-1)
                    except:
                        print(self.name)
            if nrInputs == 2:
                if len(vector1) and len(vector2):
                    u = vector1
                    v = vector2
                    leve = levelsOflist(u)
                    try:
                        result = self.recurse_fxy(u, v, scalar_out[self.items_][0], leve-1)
                    except:
                        print(self.name)
            SvSetSocketAnyType(self, 'out', result)

    # apply f to all values recursively
    def recurse_fx(self, l, f, leve):
        if not leve:
            w = f(Vector(l))
            if self.scalar_output_socket:
                return w
            else:
                return w.to_tuple()
        else:
            t = []
            for i in l:
                t.append(self.recurse_fx(i, f, leve-1))
        return t

    # match length of lists,
    # taken from mathNode
    def recurse_fxy(self, l1, l2, f, leve):
        if not leve:
                w = f(Vector(l1), Vector(l2))
                if self.scalar_output_socket:
                    return w
                else:
                    return w.to_tuple()
        else:
            max_obj = max(len(l1), len(l2))
            fullList(l1, max_obj)
            fullList(l2, max_obj)
            res = []
            for i in range(len(l1)):
                res.append(self.recurse_fxy(l1[i], l2[i], f, leve-1))
            return res

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(VectorMathNode)


def unregister():
    bpy.utils.unregister_class(VectorMathNode)
