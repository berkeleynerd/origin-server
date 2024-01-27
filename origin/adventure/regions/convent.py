# coding=utf-8

from origin.objects.exits.Exit import Exit
from origin.objects.exits.doors.Door import Door
from origin.objects.items.containers.Box import Box
from origin.objects.items.keys.Key import Key
from origin.objects.items.Item import Item
from origin.objects.items.standard.Note import Note
from origin.objects.locations.Location import Location
from origin.objects.locations.GameEnd import GameEnd
from origin.objects.creatures.npcs.Bastet import Bastet


#
# Called when region is first loaded
#
def init(engine):
    pass


#
# create the various locations in the region
#

cupola = Location("COPTIC CONVENT",
                  "You stand inside a small dome-like structure within the Coptic Convent of St. Demiana in Abydos, " 
                  "Egypt. A large ornate wrought iron chandelier featuring glowing incandescent bulbs augments the " 
                  "light of the morning sun already streaming in  through the stained glass windows that adorn the "
                  "dome. Behind you, a thick door made of Lebanese cedar stands closed, secured by a black wrought "
                  "iron handle that latches but does not appear to lock. Directly opposite the door, and thus before "
                  "you, a broad stairwell leads down. To either side of the stairwell are set Christocentric icons "
                  "intended to elevate the soul of the believer.",
                  "convent",
                  "cupola")

garden = Location("CHURCHYARD",
                  "Gardens in the desert this far from the river are rare and this specimen is particularly "
                  "verdant considering there is no apparent irrigation system. "
                  "In some ways the churchyard resembles more a meadow than a garden, with flowers "
                  "and grasses growing in the shade of huge date palm and sycamore trees. Meandering between "
                  "them a dusty path leads eventually through a waist-high wrought iron fence.", "convent", "garden")

cemetery = Location("CEMETERY",
                    "Beyond the garden a short iron fence marks the beginning of a small cemetery that stretches "
                    "through the remainder of the garden and eventually spills out into the desert. Amidst "
                    "the peaceful scene you notice among the gravestones a dark, rectangular, stone-lined hole in the ground. "
                    "Peering into it you see a stone stairway leading down.")

chamber = Location("CHAMBER",
                   "The dim light reveals a rectangular chamber about thirty feet long with an arched ceiling "
                   "made of hewn stone. The floor is laid with flagstones and in the center a red carpet runs "
                   "from the entrance to a low platform upon which sits a magnificent golden throne, like a "
                   "king's throne from a fairy tale. Upon the thrown sits what appears to be a tree trunk "
                   "twelve to fifteen feet high and about one and a half to two feet thick that reaches "
                   "almost to the ceiling. Upon closer inspection the tree trunk appears to be man made with "
                   "a fleshy appearance that looks all too real. It's top appears to be shaped into something "
                   "round like a head with no face and no hair. At its pinnacle the head has a sort of single "
                   "eye, gazing motionlessly upward. Above the head there is a peculiar aura of brightness, "
                   "although there are no windows and no apparent source of light other than that streaming "
                   "in from beyond the curtain. The thing on the throne does not move, yet you have the "
                   "feeling that it might at any moment crawl off the throne like a worm and creep toward you.")

cupolaStairwell = Location(name="STAIRWELL",
                           description="A broad stairwell terminating in a locked room.",
                           region="convent",
                           varname="cupolaStairwell")

fortress = GameEnd("REWORKED FORT", "TBD", varname="fortress")

# At the bottom of the stairwell a portal with a round arch is blocked by a sumptuous green curtain made of a
# heavy worked fabric like brocade.

#
# Create the exits connecting the locations
#


cupolaToGarden_Door = Door(["garden", "door", "outside"],
                           garden,
                           "A door leads to the garden outside the convent.",
                           "There's a thick, heavy door here made of Lebanese cedar that leads to the garden outside "
                           "the convent.",
                           locked=False,
                           opened=False)

cupolaToGarden_Door.code = 1

gardenToCupola_Door = cupolaToGarden_Door.reverse_door(
    ["cupola", "convent", "door", "inside"],
    cupola,
    "A door leads to the cupola inside the convent.",
    "There's a thick, heavy door here made of Lebanese cedar that leads to the garden outside the convent.")


gardenToCemetary_Path = Exit(
    ["cemetery", "path", "fence"],
    cemetery,
    "A dusty path leads to a cemetery just beyond the garden's edge.")

cemeteryToGarden_Path = Exit(
    ["garden", "path", "fence"],
    garden,
    "A dusty path leads back to the garden just outside the convent.")

# You can also create an exit with a bound target inline (expressed as an object):
#
# cupola.add_exits([Exit(["stairwell", "down"], cupolaStairwell, "You can see the stairwell from here.")])
# cupolaStairwell.add_exits([Exit(["cupola", "up"], cupola, "You can see the interior of the cupola from here.")])
#
# ...or as a string and the engine will automatically create the link from the unbound target.
#
# garden_exit = Exit("garden_exit", "house.garden", "There's a door to the garden here.")

cupolaToStairwell = Exit(
    ["stairwell", "down"],
    cupolaStairwell,
    "A dusty path leads to a cemetery just beyond the garden's edge.")

stairwellToCupola = Exit(
    ["cupola", "up"],
    cupola,
    "You can see the interior of the cupola from here.")

stairwellToFortress_Door = Door(
    ["fortress", "door"],
    fortress,
    "A door leads to the ruins of an ancient Egyptian fortress above which the cupola was built. "
    "There's a thick, heavy door here made of Lebanese cedar that connects the now mostly subterranean ruins of the "
    "ancient Egyptian fortress the cupola was built atop.",
    locked=True,
    opened=False)

stairwellToFortress_Door.code = 2

fortressToStairwell_Door = stairwellToFortress_Door.reverse_door(
    ["stairwell", "door"],
    cupolaStairwell,
    "A door leads to the stairwell inside the convent.",
    "There's a thick, heavy door here made of Lebanese cedar that connects the now mostly subterranean ruins of the "
    "ancient Egyptian fortress the cupola was built atop.")

cupola.add_exits([cupolaToStairwell])
cupolaStairwell.add_exits([stairwellToCupola])

garden.add_exits([gardenToCemetary_Path])
cemetery.add_exits([cemeteryToGarden_Path])

cupola.add_exits([cupolaToGarden_Door])
garden.add_exits([gardenToCupola_Door])

fortress.add_exits([fortressToStairwell_Door])
cupolaStairwell.add_exits([stairwellToFortress_Door])

#
# Create NPCs
#

bastet = Bastet("bastet",
             "f",
             None,
             "You eye Bastet a little wearily at first as she's a rather large, "
             "strong looking, spotted cat with very long legs. She could take care "
             "of herself in a fight. Her face seems intelligent and peaceful "
             "though, and she looks happy to see you. It's probably safe to pet Bastet.",
             None)

#
# Create Items
#

key = Key("key",
          "small bronze key",
          "This key is small and bronze and looks very old indeed. It has a label on a string attached that reads "
          "\"fortress door\".")

key.doorKey(stairwellToFortress_Door)


chest = Box("chest",
            "heavy jade chest")


rock = Item("rock",
            "peculiar rock",
            "A small rock with peculiar scratches that could represent a kind of mark or symbol.")

# e.g., newspaper = Note("shopping list", description="Looks to be a shopping list")
#       newspaper.text = "Tooth Brush", "Tooth Paste", "Dental Floss"
#       newspaper.aliases.add("note")

stellae = Note("thin stone slab", description="A thin slab of green dolomite with strange"
                                              " characters written on it")
stellae.aliases.add("stone")
stellae.aliases.add("slab")
stellae.aliases.add("stellae")

stellae.text = "<esoteric>𓆓 𓂧 𓇋 𓈖 𓌞 𓅱 𓀀 𓇋 𓈎 𓂋 𓏛</esoteric>\v"
stellae.text += "<translation>An excellent follower says:</translation>\n"
stellae.text += "<esoteric>𓅱 𓍑 𓄿 𓏛 𓄣 𓏤 𓎡 𓄂 𓂝 𓀀</esoteric>\v"
stellae.text += "<translation>May it please you, count,</translation>\n"
stellae.text += "<esoteric>𓅓 𓂝 𓎡 𓄖 𓂻 𓈖 𓈖 𓏥 𓄚 𓈖 𓏌 𓅱 𓉐</esoteric>\v"
stellae.text += "<translation>we have reached home,</translation>\n"
stellae.text += "<esoteric>𓅱 𓉐 𓊏 𓊪 𓂝 𓐍 𓂋 𓊪 𓏲𓆱</esoteric>\v"
stellae.text += "<translation>the maul has been taken,</translation>\n"
stellae.text += "<esoteric>𓎛 𓀝 𓀜 𓏠 𓈖 𓇋 𓏏 𓊧 𓆱</esoteric>\v"
stellae.text += "<translation>the mooring post has been driven in,</translation>\n"
stellae.text += "<esoteric>𓄂 𓏏 𓏏 𓏲 𓂋 𓂝 𓏏 𓁷 𓏤 𓇾 𓈇 𓏤</esoteric>\v"
stellae.text += "<translation>and the prow rope has been thrown on land,</translation>\n"
stellae.text += "<esoteric>𓂋 𓂝 𓎛 𓎡 𓈖 𓏌 𓏲 𓀁 𓊹 𓇼 𓄿 𓀢 𓀁</esoteric>\v"
stellae.text += "<translation>praise is given, and the god is thanked,</translation>\n"
stellae.text += "<esoteric>𓊃 𓀀 𓏤 𓎟 𓁷 𓏤 𓎛 𓊪 𓏏 𓂘 𓂝 𓌢 𓈖 𓏌 𓅱 𓀀 𓏤 𓏤 𓆑</esoteric>\v"
stellae.text += "<translation>every man is embracing his fellow</translation>\n"
stellae.text += "<esoteric>𓇩 𓅱 𓏏 𓀀 𓏤 𓏤 𓏤 𓏏 𓈖 𓏤 𓏤 𓏤 𓇍 𓇋 𓏏 𓂻 𓎙 𓂧 𓏏 𓏛</esoteric>\v"
stellae.text += "<translation>and our crew has come back safe,</translation>\n"
stellae.text += "<esoteric> 𓂜 𓈖 𓈖 𓉔 𓅱 𓅪 𓈖</esoteric>\v"
stellae.text += "<translation>without loss to our expedition.</translation>\n"



#
# Add NPCs and items to locations and inventory locations
#

cupola.insert(bastet, None)
cupola.insert(rock, None)
cupola.insert(key, None)
fortress.insert(chest, None)
fortress.insert(stellae, None)
