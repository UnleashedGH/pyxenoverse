import os

from recordclass import recordclass
import struct
from pyxenoverse import BaseRecord

BCM_SIGNATURE = b'#BCM'
BCMHeader = recordclass('BCMHeader', [
    'endianess_check',
    'u_06',
    'num_entries',
    'data_start'
])
BCM_HEADER_SIZE = 12
BCM_HEADER_BYTE_ORDER = 'HHII'

BCMEntry = recordclass('BCMEntry', [
    'address',
    'u_00',
    'directional_input',
    'button_input',
    'hold_down_conditions',
    'opponent_size_conditions', # 0x10
    'minimum_loop_duration',
    'maximum_loop_duration',
    'primary_activator_conditions', # 0x18
    'activator_state', # 0x1C
    'bac_entry_primary', # 0x20
    'bac_entry_charge', # 0x22
    'u_24',
    'bac_entry_user_connect', # 0x26
    'bac_entry_victim_connect',
    'bac_entry_airborne',
    'bac_entry_unknown',
    'random_flag',
    'sibling',
    'child',
    'parent',
    'root',
    'ki_cost',
    'u_44',
    'u_48',
    'receiver_link_id',
    'u_50',
    'stamina_cost',
    'u_58',
    'ki_required', # 5C
    'health_required', # 60
    'trans_stage', # 64

    'cus_aura', # 66
    'u_68',
    'u_6a',
    'u_6c',
])
BCM_ENTRY_SIZE = 112
BCM_ENTRY_BYTE_ORDER = 'IIIIIhhIIHHHHHHHHIIIIIIIIIIIIfh' \
                       'hHHI'

class Entry(BaseRecord):
    def __init__(self, bcm, index):
        super().__init__()
        self.bcm = bcm
        self.data = BCMEntry(*([0] * len(BCMEntry.__fields__)))
        self.comment = ""

    def read(self, f, endian, address):
        bytes_read = [address] + list(struct.unpack(endian + BCM_ENTRY_BYTE_ORDER, f.read(BCM_ENTRY_SIZE)))
        self.data= BCMEntry(*bytes_read)

    def setComment(self, cmnt):
        self.comment = cmnt.rstrip()

    def getDisplayComment(self):
        if self.comment != "" and self.comment != "\n":
            return f" - {self.comment}"
        else:
            return ""
    def getComment(self):
        if self.comment != "":
            return self.comment
        else:
            return ""


class BCM:
    def __init__(self, endian='<'):
        self.header = None
        self.endian = endian
        self.entries = []
        self.has_comments = False
        self.filename = ''

    def load(self, filename):
        with open(filename, 'rb') as f:
            if f.read(4) != BCM_SIGNATURE:
                print("Not a valid BCM file")
                return False
            self.endian = '<' if f.read(2) == b'\xFE\xFF' else '>'
            f.seek(4)
            self.read(f, self.endian)
        self.filename = filename
        return True

    def save(self, filename=None):
        if filename:
            self.filename = filename
        with open(self.filename, 'wb') as f:
            f.write(BCM_SIGNATURE)
            self.write(f, '<')

    def loadComment(self, filename):
        #comment

        filename = filename[0:-4]
        filename = filename + "_BCM.cmnt"


        if not os.path.exists(filename):
            #print("does not exists")
            return

        print(self.entries)
        try:

            with open(filename, 'r') as f:
                comments = f.readlines()
                self.has_comments = True
                if self.entries:
                    for i, entry in enumerate(self.entries):

                        entry.setComment(comments[i])
        except:
            print("failed to load comment data, file might be empty or incorrectly formatted")
            return



    def saveComment(self, fileName=None):
        if not self.has_comments:
            return
        fileName = fileName[0:-4]
        fileName = fileName + "_BCM.cmnt"
        cmnt_list = []
        try:
            with open(fileName, 'w') as f:
                for entry in self.entries:

                    cmnt_list.append(entry.getComment() + "\n")
                f.writelines(cmnt_list)
        except:
            print("failed to save comment data")
            return



    def read(self, f, endian):
        # Header
        self.header = BCMHeader(*struct.unpack(endian + BCM_HEADER_BYTE_ORDER, f.read(BCM_HEADER_SIZE)))
        f.seek(self.header.data_start)
        self.entries.clear()
        for idx in range(self.header.num_entries):
            address = f.tell() if idx != 0 else 0

            entry = Entry(self, idx)
            entry.read(f, endian, address)
            #entry = BCMEntry(*bytes_read)
            self.entries.append(entry)

    def write(self, f, endian):
        self.header.num_entries = len(self.entries)
        self.header.data_start = 16  # never changes
        f.write(struct.pack(endian + BCM_HEADER_BYTE_ORDER, *self.header))
        f.seek(self.header.data_start)
        for idx, entry in enumerate(self.entries):
            f.seek(entry.address if idx != 0 else self.header.data_start)
            f.write(struct.pack(endian + BCM_ENTRY_BYTE_ORDER, *entry.data[1:]))



def index_to_address(index):
    if not index:
        return 0
    return (index * BCM_ENTRY_SIZE) + (BCM_HEADER_SIZE + 4)


def address_to_index(address):
    if not address:
        return 0
    return int((address - (BCM_HEADER_SIZE + 4)) / BCM_ENTRY_SIZE)




