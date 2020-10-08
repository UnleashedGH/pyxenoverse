from collections import defaultdict
import struct
from recordclass import recordclass

from pyxenoverse import BaseRecord
from pyxenoverse.bsa.collision import Collision, BSA_COLLISION_SIZE
from pyxenoverse.bsa.expiration import Expiration, BSA_EXPIRATION_SIZE
from pyxenoverse.bsa.sub_entry import SubEntry, BSA_SUB_ENTRY_SIZE

BSAEntry = recordclass('BSAEntry', [
    'i_00',
    'collision_count',
    'expiration_count',
    'collision_offset',
    'expiration_offset',
    'impact_properties',
    'i_17',
    'i_18',
    'lifetime',
    'i_24',
    'expires',
    'impact_projectile',
    'impact_enemy',
    'impact_ground',
    'sub_entry_count',
    'sub_entry_offset',
    'i_40',
    'i_44',
    'i_48',
])


BSA_ENTRY_HEADER_SIZE = 52
BSA_ENTRY_HEADER_BYTE_ORDER = 'IHHIIBBIHHHHHHHIIII'


class Entry(BaseRecord):
    def __init__(self, index):
        super().__init__()
        self.index = index
        self.collisions = []
        self.expirations = []
        self.sub_entries = []
        self.data = BSAEntry(*([0] * len(BSAEntry.__fields__)))

    def read(self, f, endian):
        self.data = BSAEntry(*struct.unpack(endian + BSA_ENTRY_HEADER_BYTE_ORDER, f.read(BSA_ENTRY_HEADER_SIZE)))
        # print(self.data)
        for _ in range(self.collision_count):
            collision = Collision()
            collision.read(f, endian)
            self.collisions.append(collision)

        for _ in range(self.expiration_count):
            expiration = Expiration()
            expiration.read(f, endian)
            self.expirations.append(expiration)

        self.sub_entries = []
        for n in range(self.sub_entry_count):
            sub_entry = SubEntry(n)
            sub_entry.read(f, endian)
            self.sub_entries.append(sub_entry)

        for sub_entry in self.sub_entries:
            sub_entry.read_items(f, endian)

    def write(self, f, endian):
        offset = BSA_ENTRY_HEADER_SIZE
        self.collision_count = len(self.collisions)
        self.expiration_count = len(self.expirations)
        self.sub_entry_count = len(self.sub_entries)

        self.collision_offset = offset if self.collision_count else 0
        offset += BSA_COLLISION_SIZE * self.collision_count

        self.expiration_offset = offset if self.expiration_count else 0
        offset += BSA_EXPIRATION_SIZE * self.expiration_count

        self.sub_entry_offset = offset if self.sub_entry_count else 0

        f.write(struct.pack(endian + BSA_ENTRY_HEADER_BYTE_ORDER, *self.data))
        for collision in self.collisions:
            collision.write(f, endian)
        for expiration in self.expirations:
            expiration.write(f, endian)

        if not self.sub_entry_count:
            return
        current_offset = sub_entry_offset = f.tell()
        f.seek(current_offset + self.sub_entry_count * BSA_SUB_ENTRY_SIZE)
        for sub_entry in self.sub_entries:
            sub_entry.write_items(f, endian, sub_entry_offset)
            sub_entry_offset += BSA_SUB_ENTRY_SIZE

        data_end = f.tell()
        f.seek(current_offset)
        for sub_entry in self.sub_entries:
            sub_entry.write(f, endian)
        f.seek(data_end)


    def paste(self, other):
        pass
