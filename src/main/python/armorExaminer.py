# Most of this code was written by u/ParasiticUniverse and u/MrFlood360, but has been formatted and sipmlified. Ignores class items and sunset armor, as well as items already tagged for removal in DIM.

from asyncio.windows_events import NULL
from cmath import log
from msilib.schema import File
import csv
import sys
# Config options
skipMob = False
skipRes = False
skipRec = False
skipDis = False
skipInt = False
skipStr = False

testClasses = {"Warlock", "Hunter", "Titan"}

csvColumns = {}

class armorPiece:
    def __init__(self, info):
        # Set variables
        try:
            self.name = info[csvColumns.index('Name')]
            self.hash = info[csvColumns.index('Hash')]
            self.id = info[csvColumns.index('Id')]
            self.tag = info[csvColumns.index('Tag')]
            self.artifice = (info[csvColumns.index('Seasonal Mod')] == 'artifice')
            self.tier = info[csvColumns.index('Tier')]
            self.type = info[csvColumns.index('Type')]
            self.equippable = info[csvColumns.index('Equippable')]
            self.power = int(info[csvColumns.index('Power')])
            self.powerLimit = (info[csvColumns.index('Power Limit')] != "")

            #! Armor 1.0 exotics have no masterwork so this is required.
            try:
                self.masterworkTier = int(info[csvColumns.index('Energy Capacity')])
            except Exception as e:
                self.masterworkTier = 0

            self.mob = int(info[csvColumns.index('Mobility (Base)')])
            self.res = int(info[csvColumns.index('Resilience (Base)')])
            self.rec = int(info[csvColumns.index('Recovery (Base)')])
            self.dis = int(info[csvColumns.index('Discipline (Base)')])
            self.int = int(info[csvColumns.index('Intellect (Base)')])
            self.str = int(info[csvColumns.index('Strength (Base)')])
            self.total = int(info[csvColumns.index('Total (Base)')])

        except Exception as e:
            print(e)
            print("Something went wrong with " + self.name)

    # Determine if stats of two pieces are identical
    def identicalStats(self, test):
        return self.mob == test.mob and self.res == test.res and self.rec == test.rec and self.dis == test.dis and self.int == test.int and self.str == test.str

    # Determine if stats of a piece are better than stats of another piece
    def isBetter(self, test):
        # Slip class items
        if self.type == "Warlock Bond" or self.type == "Hunter Cloak" or self.type == "Titan Mark":
            return False
        # Skip different armor tiers
        if self == test or self.tier != test.tier:
            return False
        # Only compare an exotic item to itself
        if self.tier == "Exotic" and test.tier == "Exotic" and self.name != test.name:
            return False
        # Check classes and slot are the same
        if self.equippable == test.equippable and self.type == test.type and self.equippable in testClasses:
            #! Skip if stats are completely identical
            if self.identicalStats(test):
                return False
            # Check if all stats are equal to or better than test piece, respecting config options
            statNames = ['mob', 'res', 'rec', 'dis', 'int', 'str']
            # Remove unwanted stats
            for statName in statNames:
                if globals()["skip{}".format(statName.capitalize())]:
                    statNames.remove(statName)
            # Test if current armor is better
            checkList = []
            for otherStatName in statNames:
                checkList.append(self.__getattribute__(otherStatName) >= test.__getattribute__(otherStatName))
            if all(ele == True for ele in checkList):
                return True
            # Test artifice armor stat boosts
            if self.artifice:
                for statName in statNames:
                    checkList = []
                    checkList.append(self.__getattribute__(statName) + 3 >= test.__getattribute__(statName))
                    for otherStatName in [x for x in statNames if x != statName]:
                        checkList.append(self.__getattribute__(otherStatName) >= test.__getattribute__(otherStatName))
                    if all(ele == True for ele in checkList):
                        return True
        return False

    # Simpler way to print armor piece
    def shortStr(self):
        return str(self.name) + "," + str(self.equippable) + "," + str(self.type) + "," + str(self.power) + "," + str(self.total) + "," + str(self.masterworkTier) + "," + str(self.id)


def run():
    global skipMob, skipRec, skipRes, skipDis, skipInt, skipStr, testClasses, csvColumns
    yes = ['Y','YES']
    #Prompting and config
    print("Setup: Decide what parameters to use. Press Y for yes, any other key for no.")
    classes = input("Classes to check? W,H,T (Default: All)\n")
    skipMob = input("Ignore Mobility? Y/N (Default: No)\n").upper() in yes
    skipRes = input("Ignore Resilience? Y/N (Default: No)\n").upper() in yes
    skipRec = input("Ignore Recovery? Y/N (Default: No)\n").upper() in yes
    skipDis = input("Ignore Discipline? Y/N (Default: No)\n").upper() in yes
    skipInt = input("Ignore Intellect? Y/N (Default: No)\n").upper() in yes
    skipStr = input("Ignore Strength? Y/N (Default: No)\n").upper() in yes

    if len(classes) > 0:
        if "W" not in str(classes).upper():
            testClasses.remove("Warlock")
        if "H" not in str(classes).upper():
            testClasses.remove("Hunter")
        if "T" not in str(classes).upper():
            testClasses.remove("Titan")

    # Open CSV from DIM
    with open('input/destinyArmor.csv', newline='', errors="ignore") as f:
        reader = csv.reader(f)
        rawArmorList = list(reader)
        armorList = []
        
        csvColumns = rawArmorList[0]
        # List of all pieces
        for currentArmor in rawArmorList[1:]:
            if armorPiece(currentArmor).tag not in {"junk", "infuse"}:
                armorList.append(armorPiece(currentArmor))

        # Create list of comparisons
        superiorityList = []
        for currentArmor in armorList:
            for testArmor in armorList:
                if currentArmor.isBetter(testArmor) and testArmor.powerLimit == False:
                    superiorityList.append((currentArmor, testArmor))

        # Lists of armor to keep and shard
        bestArmor = list(set([armor[0] for armor in superiorityList]))
        worstArmor = list(set([armor[1] for armor in superiorityList]))

        simpleSuperiorityList = []

        # Formatting the list so that each piece to keep is listed next to which pieces it supersedes
        for currentArmor in bestArmor:
            badArmorList = [
                armor[1] for armor in superiorityList
                if armor[0] == currentArmor
            ]
            simpleSuperiorityList.append([currentArmor, badArmorList])

        # Display
        original_stdout = sys.stdout
        with open('output/ArmorExamined.txt', 'w') as f:
            sys.stdout = f
            for betterArmorPiece in simpleSuperiorityList:
                for worseArmorPiece in betterArmorPiece[1]:
                    print(f'id:{betterArmorPiece[0].id} or id:{worseArmorPiece.id}')
                    printformatted(betterArmorPiece[0], worseArmorPiece)
            print("Vault Spaces Saveable: " + str(len(list(set(worstArmor)))), end="\n\n")

            armorSet = set()
            printstr = "DIM string for items to delete:      \n"
            for betterArmorPiece in simpleSuperiorityList:
                for worseArmorPiece in betterArmorPiece[1]:
                    if worseArmorPiece not in armorSet:
                        armorSet.add(worseArmorPiece)
                        printstr += f'id:{worseArmorPiece.id} or '
            print(printstr[0:len(printstr)-4])

        sys.stdout = original_stdout  #? Reset the standard output to its original value


def printformatted(better, worse):
    print("%s : %s (%s %s at %s power) > \n%s : %s (%s %s at %s power)\n" %
          (better.id, better.name, better.equippable, better.type, better.power, worse.id, worse.name, worse.equippable, worse.type, worse.power))


if __name__ == "__main__":
    run()
